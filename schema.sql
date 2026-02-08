-- ==========================================================
-- SAFE / IDEMPOTENT SCHEMA (WON'T DROP DATA)
-- - Creates types only if not exists
-- - Creates tables only if not exists
-- - Creates views using OR REPLACE
-- ==========================================================

-- 1) ENUM types (create only if they don't exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'student', 'instructor');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'course_type') THEN
        CREATE TYPE course_type AS ENUM ('degree', 'diploma', 'certificate');
    END IF;
END $$;

-- 2) USERS (Superclass)
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    role user_role NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3) Admin
CREATE TABLE IF NOT EXISTS Admins (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 4) Analyst
CREATE TABLE IF NOT EXISTS Analysts (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 5) Student
CREATE TABLE IF NOT EXISTS Students (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE,
    age INT CHECK (age > 0),
    skill_level VARCHAR(50),
    country VARCHAR(100)
);

-- 6) Instructor
CREATE TABLE IF NOT EXISTS Instructors (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    bio VARCHAR(500)
);

-- 7) Universities
CREATE TABLE IF NOT EXISTS Universities (
    uni_id SERIAL PRIMARY KEY,
    uni_name VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    uni_type VARCHAR(50)
);

-- 8) Courses
CREATE TABLE IF NOT EXISTS Courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) UNIQUE NOT NULL,
    duration_weeks INT,
    c_type course_type,
    uni_id INT NOT NULL REFERENCES Universities(uni_id) ON DELETE CASCADE
);

-- 9) Topics
CREATE TABLE IF NOT EXISTS Topics (
    topic_id SERIAL PRIMARY KEY,
    topic_name VARCHAR(100) NOT NULL
);

-- 10) Course_Topics
CREATE TABLE IF NOT EXISTS Course_Topics (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    topic_id INT REFERENCES Topics(topic_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, topic_id)
);

-- 11) TextBooks
CREATE TABLE IF NOT EXISTS TextBooks (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255)
);

-- 12) Course_TextBooks
CREATE TABLE IF NOT EXISTS Course_TextBooks (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    book_id INT REFERENCES TextBooks(book_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, book_id)
);

-- 13) Enrollments
CREATE TABLE IF NOT EXISTS Enrollments (
    student_id INT REFERENCES Students(user_id) ON DELETE CASCADE,
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    grade DECIMAL(5, 2) CHECK (grade >= 0 AND grade <= 100),
    due_by DATE,
    PRIMARY KEY (student_id, course_id)
);

-- 14) Course_Instructors
CREATE TABLE IF NOT EXISTS Course_Instructors (
    instructor_id INT REFERENCES Instructors(user_id) ON DELETE CASCADE,
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    PRIMARY KEY (instructor_id, course_id)
);

-- 15) CourseVideos
CREATE TABLE IF NOT EXISTS CourseVideos (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    video_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id, video_url)
);

-- 16) CourseNotes
CREATE TABLE IF NOT EXISTS CourseNotes (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    note_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    format VARCHAR(10) DEFAULT 'PDF',
    PRIMARY KEY (course_id, note_url)
);

-- 17) CourseOnlineBooks
CREATE TABLE IF NOT EXISTS CourseOnlineBooks (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    book_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    page_count INT,
    PRIMARY KEY (course_id, book_url)
);

-- ==========================================================
-- VIEWS (safe: updates view definition without deleting data)
-- ==========================================================

CREATE OR REPLACE VIEW student_courses AS
SELECT
    c.course_id,
    c.course_name,
    c.duration_weeks,
    c.c_type,
    u.uni_name AS university_name,
    u.city AS university_city,
    u.country AS university_country
FROM Courses c
JOIN Universities u ON c.uni_id = u.uni_id;

CREATE OR REPLACE VIEW instructor_assigned_courses AS
SELECT
    ci.instructor_id,
    c.course_id,
    c.course_name,
    c.duration_weeks,
    c.c_type,
    u.uni_name AS university_name
FROM Course_Instructors ci
JOIN Courses c ON ci.course_id = c.course_id
JOIN Universities u ON c.uni_id = u.uni_id;

CREATE OR REPLACE VIEW course_statistics AS
SELECT
    c.course_id,
    c.course_name,
    COUNT(e.student_id) AS total_enrollments,
    AVG(e.grade) AS average_grade
FROM Courses c
LEFT JOIN Enrollments e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name;
