-- 1. Create ENUM types for better data consistency
CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'student', 'instructor');
CREATE TYPE course_type AS ENUM ('degree', 'diploma', 'certificate');

-- 2. Base Table: USERS (Superclass)
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    role user_role NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Subclass: Admin
CREATE TABLE Admins (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 4. Subclass: Analyst
CREATE TABLE Analysts (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 5. Subclass: Student
CREATE TABLE Students (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE,
    age INT CHECK (age > 0),
    skill_level VARCHAR(50), -- e.g., 'Beginner', 'Intermediate'
    country VARCHAR(100)
);

-- 6. Subclass: Instructor
CREATE TABLE Instructors (
    user_id INT PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    bio VARCHAR(500)
);

-- 7. Universities (Partner Universities)
CREATE TABLE Universities (
    uni_id SERIAL PRIMARY KEY,
    uni_name VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    uni_type VARCHAR(50) -- e.g., 'Public', 'Private'
);

-- 8. Courses
-- Constraint 2: A course has exactly one partner university (NOT NULL FK)
-- Constraint 6: Every course name is unique
CREATE TABLE Courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) UNIQUE NOT NULL,
    duration_weeks INT,
    c_type course_type,
    uni_id INT NOT NULL REFERENCES Universities(uni_id) ON DELETE CASCADE
);

-- 9. Topics
CREATE TABLE Topics (
    topic_id SERIAL PRIMARY KEY,
    topic_name VARCHAR(100) NOT NULL
    -- duration_hours INT
);

-- Junction Table for Courses <-> Topics (M:N)
-- Constraint 1: A course can have one or more topics
CREATE TABLE Course_Topics (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    topic_id INT REFERENCES Topics(topic_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, topic_id)
);

-- 10. TextBooks (Physical/Reference Books from Diagram)
CREATE TABLE TextBooks (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255)
);

-- Junction Table for Courses <-> TextBooks (N:M)
CREATE TABLE Course_TextBooks (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    book_id INT REFERENCES TextBooks(book_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, book_id)
);

-- 11. Enrollments (Student <-> Course)
-- Constraint 3: Evaluation value range 0-100
CREATE TABLE Enrollments (
    student_id INT REFERENCES Students(user_id) ON DELETE CASCADE,
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    grade DECIMAL(5, 2) CHECK (grade >= 0 AND grade <= 100),
    due_by DATE,
    PRIMARY KEY (student_id, course_id)
);

-- 12. Teaching Assignments (Instructor <-> Course)
CREATE TABLE Course_Instructors (
    instructor_id INT REFERENCES Instructors(user_id) ON DELETE CASCADE,
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    PRIMARY KEY (instructor_id, course_id)
);

-- ==========================================
-- THE UPGRADE: Split Weak Entities for Content
-- Partial Key: url
-- Weak Entity PK: (course_id, url)
-- ==========================================

-- 13. Course Videos (Weak Entity)
CREATE TABLE CourseVideos (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    video_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL, -- "Video also has duration"
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id, video_url)
);

-- 14. Course Notes (Weak Entity)
CREATE TABLE CourseNotes (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    note_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    format VARCHAR(10) DEFAULT 'PDF', -- Added useful attribute
    PRIMARY KEY (course_id, note_url)
);

-- 15. Course Online Books (Weak Entity - Distinct from TextBooks entity)
-- "Books" as requested in content split
CREATE TABLE CourseOnlineBooks (
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,
    book_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    page_count INT, -- Added useful attribute
    PRIMARY KEY (course_id, book_url)
);

-- ==========================================
-- ROLE-BASED ACCESS CONTROL (RBAC) DEFINITIONS
-- ==========================================

-- 1. Create Application Roles
-- These roles are for managing database privileges and should be granted to
-- specific database users (e.g., 'application_user_admin', 'application_user_analyst')
-- that your application connects with.

-- CREATE ROLE app_admin;
-- CREATE ROLE app_analyst;

-- 2. Grant Permissions to app_admin
-- app_admin has full control over all tables. This role is intended for users
-- or application processes that require full read, write, and schema modification
-- capabilities.

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_admin;

-- 3. Grant Permissions to app_analyst
-- app_analyst has read-only access (SELECT) to all tables. This role is intended
-- for users or application processes that only need to view data,
-- without the ability to modify it.

-- GRANT SELECT ON TABLE Users TO app_analyst;
-- GRANT SELECT ON TABLE Admins TO app_analyst;
-- GRANT SELECT ON TABLE Analysts TO app_analyst;
-- GRANT SELECT ON TABLE Students TO app_analyst;
-- GRANT SELECT ON TABLE Instructors TO app_analyst;
-- GRANT SELECT ON TABLE Universities TO app_analyst;
-- GRANT SELECT ON TABLE Courses TO app_analyst;
-- GRANT SELECT ON TABLE Topics TO app_analyst;
-- GRANT SELECT ON TABLE Course_Topics TO app_analyst;
-- GRANT SELECT ON TABLE TextBooks TO app_analyst;
-- GRANT SELECT ON TABLE Course_TextBooks TO app_analyst;
-- GRANT SELECT ON TABLE Enrollments TO app_analyst;
-- GRANT SELECT ON TABLE Course_Instructors TO app_analyst;
-- GRANT SELECT ON TABLE CourseVideos TO app_analyst;
-- GRANT SELECT ON TABLE CourseNotes TO app_analyst;
-- GRANT SELECT ON TABLE CourseOnlineBooks TO app_analyst;

-- -- 4. Grant Permissions to app_student
-- -- app_student has read-only access to course information and can insert into enrollments.
-- CREATE ROLE app_student;
-- GRANT SELECT ON TABLE Courses TO app_student;
-- GRANT SELECT ON TABLE Topics TO app_student;
-- GRANT SELECT ON TABLE Universities TO app_student;
-- GRANT SELECT ON TABLE TextBooks TO app_student;
-- GRANT SELECT ON TABLE Course_Topics TO app_student;
-- GRANT SELECT ON TABLE Course_TextBooks TO app_student;
-- GRANT SELECT ON TABLE CourseVideos TO app_student;
-- GRANT SELECT ON TABLE CourseNotes TO app_student;
-- GRANT SELECT ON TABLE CourseOnlineBooks TO app_student;
-- GRANT INSERT ON TABLE Enrollments TO app_student; -- For students to register themselves

-- -- 5. Grant Permissions to app_instructor
-- -- app_instructor has read access to relevant course info and can manage course content.
-- CREATE ROLE app_instructor;
-- GRANT SELECT ON TABLE Courses TO app_instructor;
-- GRANT SELECT ON TABLE Topics TO app_instructor;
-- GRANT SELECT ON TABLE Universities TO app_instructor;
-- GRANT SELECT ON TABLE TextBooks TO app_instructor;
-- GRANT SELECT ON TABLE Course_Instructors TO app_instructor; -- To see their assigned courses
-- GRANT INSERT, UPDATE, DELETE ON TABLE CourseVideos TO app_instructor;
-- GRANT INSERT, UPDATE, DELETE ON TABLE CourseNotes TO app_instructor;
-- GRANT INSERT, UPDATE, DELETE ON TABLE CourseOnlineBooks TO app_instructor;
-- -- Note: Granular control (e.g., instructors only managing content for their own courses)
-- -- should be enforced at the application layer.

-- ==========================================
-- ROLE-SPECIFIC VIEWS
-- ==========================================

-- View for Students: student_courses
-- Allows students to see available courses and basic information.
CREATE VIEW student_courses AS
SELECT
    c.course_id,
    c.course_name,
    c.duration_weeks,
    c.c_type,
    u.uni_name AS university_name,
    u.city AS university_city,
    u.country AS university_country
FROM
    Courses c
JOIN
    Universities u ON c.uni_id = u.uni_id;

-- Grant access to the student view
-- GRANT SELECT ON student_courses TO app_student;

-- View for Instructors: instructor_assigned_courses
-- Allows instructors to see courses they are assigned to.
CREATE VIEW instructor_assigned_courses AS
SELECT
    ci.instructor_id,
    c.course_id,
    c.course_name,
    c.duration_weeks,
    c.c_type,
    u.uni_name AS university_name
FROM
    Course_Instructors ci
JOIN
    Courses c ON ci.course_id = c.course_id
JOIN
    Universities u ON c.uni_id = u.uni_id;

-- Grant access to the instructor view
-- GRANT SELECT ON instructor_assigned_courses TO app_instructor;

-- View for Data Analysts: course_statistics (example)
-- A more complex view for analysts to get aggregated data.
-- This is a placeholder; actual statistics would be more detailed.
CREATE VIEW course_statistics AS
SELECT
    c.course_id,
    c.course_name,
    COUNT(e.student_id) AS total_enrollments,
    AVG(e.grade) AS average_grade
FROM
    Courses c
LEFT JOIN
    Enrollments e ON c.course_id = e.course_id
GROUP BY
    c.course_id, c.course_name;

-- Grant access to the analyst view
-- GRANT SELECT ON course_statistics TO app_analyst;

-- Alternatively, for future tables, you can set default privileges:
-- ALTER DEFAULT PRIVILEGES FOR ROLE app_admin IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO app_admin;
-- ALTER DEFAULT PRIVILEGES FOR ROLE app_analyst IN SCHEMA public GRANT SELECT ON TABLES TO app_analyst;

-- Example of how to assign these roles to actual database users:
-- CREATE USER your_app_admin_user WITH PASSWORD 'secure_password';
-- GRANT app_admin TO your_app_admin_user;

-- CREATE USER your_app_analyst_user WITH PASSWORD 'another_secure_password';
-- GRANT app_analyst TO your_app_analyst_user;