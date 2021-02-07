from datetime import datetime
import sys

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Therapist, Method, DataHistory
from settings import AIRTABLE_API_URL, AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, \
    AIRTABLE_REQUEST_TIMEOUT, DB_TYPE, PG_HOST, PG_PORT, PG_USERNAME, PG_PASSWORD, PG_DATABASE


class MetaUploader:
    api_url = AIRTABLE_API_URL
    timeout = AIRTABLE_REQUEST_TIMEOUT

    if DB_TYPE == 'postgresql':
        engine = create_engine(f'postgresql://{PG_USERNAME}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}',
                               echo=False)
    elif DB_TYPE == 'sqlite':
        engine = create_engine('sqlite:///test.db',
                               echo=False)
    else:
        sys.exit('DB type error. Check your settings.')

    Session = sessionmaker(bind=engine)
    session = Session()

    def __init__(self, api_key, base_id, table_name):
        self.api_key = api_key
        self.base_id = base_id
        self.table_name = table_name
        self._added = 0
        self._deleted = 0
        self._updated = 0
        Base.metadata.create_all(self.engine)

    def get_data(self):
        """
        Gets data from Airtable.

        :return:
            JSON data.
        """
        url = f'{self.api_url}/{self.base_id}/{self.table_name}'
        headers = {'Authorization': f'Bearer {self.api_key}'}

        try:
            data = requests.get(url=url, headers=headers, timeout=self.timeout)
        except requests.exceptions.Timeout:
            sys.exit('Request timeout. Try another time.')

        if data.status_code == 200:
            json_data = data.json()['records']
        else:
            sys.exit(f'Returned status code {data.status_code}. Try another time.')
        return json_data

    def get_history_data(self, date: datetime.date):
        """
        Gets history data from DB for specified date. If there are several records for date, then returns the last one.

        :param date:
            Datetime.date object.
        :return:
            JSON data or None.
        """
        if DB_TYPE == 'sqlite':
            date = date.strftime('%Y-%m-%d')

        history_data = self.session.query(DataHistory.raw_data).filter_by(date=date).all()
        if history_data:
            return history_data[-1][0]

    def _save_raw_data(self, data):
        """
        Saves raw data to DB.

        :param data:
            Airtable data.
        :return:
            None.
        """
        self.session.add(DataHistory(date=datetime.utcnow().date(), raw_data=str(data)))
        self.session.commit()

    def _update_methods(self, data):
        """
        Checks for existing therapy methods in DB and adds new from Airtable.

        :param data:
            Airtable data.
        :return:
            None.
        """
        db_methods = self.session.query(Method).all()
        db_methods = {method.name for method in db_methods}

        methods = set()
        for unit in data:
            methods_to_add = unit['fields'].get('Методы')
            if methods_to_add is not None:
                methods.update(methods_to_add)

        methods = methods.difference(db_methods)
        self.session.add_all([Method(name=method) for method in methods])
        self.session.commit()

    def update_db(self, data):
        """
        Updates DB due to changes in Airtable.

        :param data:
            Airtable data.
        :return:
            None.
        """
        def check_for_new_records(airtable_list):
            for therapist in airtable_list:
                if self.session.query(Therapist).filter_by(id=therapist.id).one_or_none() is None:
                    self.session.add(therapist)
                    self.session.commit()
                    self._added += 1

        def check_for_deleted_records(airtable_list):
            airtable_ids = [therapist.id for therapist in airtable_list]
            therapists_to_delete = self.session.query(Therapist).filter(Therapist.id.notin_(airtable_ids)).all()

            for therapist in therapists_to_delete:
                self.session.delete(therapist)
                self.session.commit()
                self._deleted += 1

        def check_for_updated_records(airtable_list):
            columns = ['name', 'photo_url', 'methods']

            for airtable_therapist in airtable_list:
                db_therapist = self.session.query(Therapist).filter_by(id=airtable_therapist.id).one()
                is_updated = False
                for column in columns:
                    if column == 'methods':  # because can't directly compare methods
                        if hash(tuple(set(airtable_therapist.methods))) != hash(tuple(set(db_therapist.methods))):
                            db_therapist.methods = airtable_therapist.methods
                            self.session.commit()
                            is_updated = True
                            continue
                    if getattr(airtable_therapist, column) != getattr(db_therapist, column):
                        setattr(db_therapist, column, getattr(airtable_therapist, column))
                        self.session.commit()
                        is_updated = True
                if is_updated:
                    self._updated += 1

        self._save_raw_data(data)
        self._update_methods(data)

        # Transforming Airtable data to Therapists objects
        airtable_therapists = []
        for unit in data:
            id_ = unit['fields']['ID']
            name = unit['fields']['Имя'] if unit['fields'].get('Имя') else ''
            photo_url = unit['fields']['Фотография'][0]['url'] if unit['fields'].get('Фотография') else ''
            unit_methods = unit['fields']['Методы'] if unit['fields'].get('Методы') else []
            methods = self.session.query(Method).filter(Method.name.in_(unit_methods)).all()
            airtable_therapists.append(
                Therapist(
                    id=id_,
                    name=name,
                    photo_url=photo_url,
                    methods=methods,
                )
            )

        # Performing checks
        check_for_deleted_records(airtable_therapists)
        check_for_new_records(airtable_therapists)
        check_for_updated_records(airtable_therapists)

    def statisitcs(self):
        """
        Returns information about uploader work.

        :return:
            Tuple with info about added, updated and deleted records.
        """
        statistics = {'added': self._added,
                      'updated': self._updated,
                      'deleted': self._deleted,
                      }
        return statistics


def main():
    uploader = MetaUploader(api_key=AIRTABLE_API_KEY, base_id=AIRTABLE_BASE_ID, table_name=AIRTABLE_TABLE_NAME)
    data = uploader.get_data()
    uploader.update_db(data)
    statistics = uploader.statisitcs()
    print('Actual data received')
    print(f"Added records: {statistics['added']}\n"
          f"Updated records: {statistics['updated']}\n"
          f"Deleted records: {statistics['deleted']}"
          )


if __name__ == '__main__':
    main()
