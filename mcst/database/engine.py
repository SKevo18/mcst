from sqlalchemy import create_engine


DATABASE_NAME = "mcst"
ENGINE = create_engine(rf"mysql+pymysql:///{DATABASE_NAME}?charset=utf8mb4&unix_socket=/run/mysqld/mysqld.sock")
