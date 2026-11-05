
CREATE DATABASE IF NOT EXISTS studentdb;

USE studentdb;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(10),
    fullname VARCHAR(100),
    dob DATE,
    major VARCHAR(50)
);

INSERT INTO students
(student_id, fullname, dob, major)
VALUES
('SV001', 'Nguyen Van A', '2004-01-15',
 'Information Technology'),
('SV002', 'Tran Thi B', '2004-05-22',
 'Computer Science'),
('SV003', 'Le Van C', '2004-08-10',
 'Software Engineering');
