# uname() error回避
import platform
print("platform", platform.uname())
 

from sqlalchemy import create_engine, insert, delete, update, select
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import json
import pandas as pd

from db_control.connect import engine
 

def myinsert(mymodel, values):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()

    query = insert(mymodel).values(values)
    try:
        # トランザクションを開始
        with session.begin():
            # データの挿入
            result = session.execute(query)
    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")
        session.rollback()
 
    # セッションを閉じる
    session.close()
    return "inserted"
 
def myselect(mymodel, filter_field: str, filter_value):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        with session.begin():
            column = getattr(mymodel, filter_field)
            query = session.query(mymodel).filter(column == filter_value)
            result = query.all()
            result_dict = [row.__dict__ for row in result]
            for row in result_dict:
                row.pop('_sa_instance_state', None)
            result_json = json.dumps(result_dict, ensure_ascii=False)
    except Exception as e:
        print("エラー:", e)
        result_json = None
    finally:
        session.close()
    return result_json


def myselectAll(mymodel):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()
    query = select(mymodel)
    try:
        # トランザクションを開始
        with session.begin():
            df = pd.read_sql_query(query, con=engine)
            result_json = df.to_json(orient='records', force_ascii=False)

    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")
        result_json = None

    # セッションを閉じる
    session.close()
    return result_json

def myupdate(mymodel, key_field: str, values: dict):
    Session = sessionmaker(bind=engine)
    session = Session()

    key_value = values.pop(key_field)
    try:
        with session.begin():
            query = update(mymodel).where(getattr(mymodel, key_field) == key_value).values(**values)
            session.execute(query)
    except Exception as e:
        print("更新エラー:", e)
        session.rollback()
    finally:
        session.close()
    return "updated"

def mydelete(mymodel, customer_id):
    # session構築
    Session = sessionmaker(bind=engine)
    session = Session()
    query = delete(mymodel).where(mymodel.customer_id==customer_id)
    try:
        # トランザクションを開始
        with session.begin():
            result = session.execute(query)
    except sqlalchemy.exc.IntegrityError:
        print("一意制約違反により、挿入に失敗しました")
        session.rollback()
 
    # セッションを閉じる
    session.close()
    return customer_id + " is deleted"