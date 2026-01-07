CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(250) NOT NULL UNIQUE,
    password VARCHAR(250) NOT NULL
);

CREATE TABLE todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content VARCHAR(100),
    due DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

/*Folgende Zeilen werden nicht automatisch ausgeführt,
wir haben sie vollständigkeitshalber trotzdem aufgeführt.*/
CREATE TABLE costumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    costume_name VARCHAR(100),
    costume_size VARCHAR(1),
    role_id INT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE actors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    actor_fname VARCHAR(30),
    actor_lname VARCHAR(30),
    actor_email VARCHAR(100),
    actor_size VARCHAR(1),
    role_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE scenes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    scene_name VARCHAR(30),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role_name VARCHAR(50) UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id),
);


