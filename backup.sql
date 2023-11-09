PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE category (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	is_income BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO category VALUES(1,'Подарки',0);
INSERT INTO category VALUES(2,'Карина',0);
CREATE TABLE month (
	id INTEGER NOT NULL, 
	name VARCHAR(20), 
	PRIMARY KEY (id)
);
CREATE TABLE year (
	id INTEGER NOT NULL, 
	value INTEGER, 
	PRIMARY KEY (id)
);
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE IF NOT EXISTS "transaction" (
	id INTEGER NOT NULL, 
	description VARCHAR(200), 
	amount FLOAT, 
	date DATE, 
	category_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES category (id)
);
COMMIT;
