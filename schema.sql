-- ==========================================================
-- SAFE / IDEMPOTENT SCHEMA (WON'T DROP DATA)
-- - Creates types only if not exists
-- - Creates tables only if not exists
-- - Adds columns only if not exists (via DO blocks)
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
CREATE TABLE IF NOT EXISTS users (
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
CREATE TABLE IF NOT EXISTS admins (
    user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE
);

-- 4) Analyst
CREATE TABLE IF NOT EXISTS analysts (
    user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE
);

-- 5) Student
CREATE TABLE IF NOT EXISTS students (
    user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    age INT CHECK (age > 0),
    skill_level VARCHAR(50),
    country VARCHAR(100)
);

-- 6) Instructor
CREATE TABLE IF NOT EXISTS instructors (
    user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    bio VARCHAR(500)
);

-- 7) Universities
CREATE TABLE IF NOT EXISTS universities (
    uni_id SERIAL PRIMARY KEY,
    uni_name VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    uni_type VARCHAR(50)
);

-- 8) Courses
CREATE TABLE IF NOT EXISTS courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) UNIQUE NOT NULL,
    duration_weeks INT,
    c_type course_type,
    uni_id INT NOT NULL REFERENCES universities(uni_id) ON DELETE CASCADE
);

-- 9) Topics (legacy - keep)
CREATE TABLE IF NOT EXISTS topics (
    topic_id SERIAL PRIMARY KEY,
    topic_name VARCHAR(100) NOT NULL
);

-- 10) Course_Topics (legacy - keep)
CREATE TABLE IF NOT EXISTS course_topics (
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    topic_id INT REFERENCES topics(topic_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, topic_id)
);

-- 11) TextBooks (legacy - keep)
CREATE TABLE IF NOT EXISTS textbooks (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255)
);

-- 12) Course_TextBooks (legacy - keep)
CREATE TABLE IF NOT EXISTS course_textbooks (
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    book_id INT REFERENCES textbooks(book_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, book_id)
);

-- 13) Enrollments (we will store marks + letter_grade here)
CREATE TABLE IF NOT EXISTS enrollments (
    student_id INT REFERENCES students(user_id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    grade DECIMAL(5, 2) CHECK (grade >= 0 AND grade <= 100),
    due_by DATE,
    PRIMARY KEY (student_id, course_id)
);

-- 13b) SAFE ALTER: add grading columns if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'enrollments' AND column_name = 'marks'
    ) THEN
        ALTER TABLE enrollments
            ADD COLUMN marks DECIMAL(5,2) CHECK (marks >= 0 AND marks <= 100);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'enrollments' AND column_name = 'letter_grade'
    ) THEN
        ALTER TABLE enrollments
            ADD COLUMN letter_grade VARCHAR(5);
    END IF;
END $$;

-- 14) Course_Instructors (admin assigns instructors to courses)
CREATE TABLE IF NOT EXISTS course_instructors (
    instructor_id INT REFERENCES instructors(user_id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    PRIMARY KEY (instructor_id, course_id)
);

-- 15) CourseVideos (legacy - keep for now)
CREATE TABLE IF NOT EXISTS coursevideos (
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    video_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id, video_url)
);

-- 16) CourseNotes (legacy - keep for now)
CREATE TABLE IF NOT EXISTS coursenotes (
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    note_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    format VARCHAR(10) DEFAULT 'PDF',
    PRIMARY KEY (course_id, note_url)
);

-- 17) CourseOnlineBooks (legacy - keep for now)
CREATE TABLE IF NOT EXISTS courseonlinebooks (
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    book_url VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    page_count INT,
    PRIMARY KEY (course_id, book_url)
);

-- ==========================================================
-- NEW STRUCTURE: Course -> Modules -> Topics -> Subtopics -> Contents
-- IMPORTANT: table names are lowercase to match SQLAlchemy __tablename__
-- ==========================================================

-- 18) coursemodules
CREATE TABLE IF NOT EXISTS coursemodules (
    module_id SERIAL PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    module_title VARCHAR(255) NOT NULL,
    module_order INT DEFAULT 1
);

-- 19) moduletopics
CREATE TABLE IF NOT EXISTS moduletopics (
    topic_id SERIAL PRIMARY KEY,
    module_id INT NOT NULL REFERENCES coursemodules(module_id) ON DELETE CASCADE,
    topic_title VARCHAR(255) NOT NULL,
    topic_order INT DEFAULT 1
);

-- 20) topicsubtopics
CREATE TABLE IF NOT EXISTS topicsubtopics (
    subtopic_id SERIAL PRIMARY KEY,
    topic_id INT NOT NULL REFERENCES moduletopics(topic_id) ON DELETE CASCADE,
    subtopic_title VARCHAR(255) NOT NULL,
    subtopic_order INT DEFAULT 1
);

-- 21) ✅ UPDATED subtopiccontents (video/notes/book)
CREATE TABLE IF NOT EXISTS subtopiccontents (
    content_id SERIAL PRIMARY KEY,
    subtopic_id INT NOT NULL REFERENCES topicsubtopics(subtopic_id) ON DELETE CASCADE,

    -- video / notes / book
    content_type VARCHAR(20) NOT NULL,

    -- common
    title VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,

    -- optional
    duration_minutes INT,
    file_format VARCHAR(20),

    content_order INT DEFAULT 1
);

-- ✅ SAFE migration if old columns exist
DO $$
BEGIN
    -- rename old columns (if they exist)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='content_title')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='title') THEN
        ALTER TABLE subtopiccontents RENAME COLUMN content_title TO title;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='link')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='url') THEN
        ALTER TABLE subtopiccontents RENAME COLUMN link TO url;
    END IF;

    -- add new columns if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='duration_minutes') THEN
        ALTER TABLE subtopiccontents ADD COLUMN duration_minutes INT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='file_format') THEN
        ALTER TABLE subtopiccontents ADD COLUMN file_format VARCHAR(20);
    END IF;

    -- drop content_text if exists (optional, because new design doesn't use it)
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subtopiccontents' AND column_name='content_text') THEN
        ALTER TABLE subtopiccontents DROP COLUMN content_text;
    END IF;
END $$;

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
FROM courses c
JOIN universities u ON c.uni_id = u.uni_id;

CREATE OR REPLACE VIEW instructor_assigned_courses AS
SELECT
    ci.instructor_id,
    c.course_id,
    c.course_name,
    c.duration_weeks,
    c.c_type,
    u.uni_name AS university_name
FROM course_instructors ci
JOIN courses c ON ci.course_id = c.course_id
JOIN universities u ON c.uni_id = u.uni_id;

-- Average should prefer marks, fallback to grade (so both work)
CREATE OR REPLACE VIEW course_statistics AS
SELECT
    c.course_id,
    c.course_name,
    COUNT(e.student_id) AS total_enrollments,
    AVG(COALESCE(e.marks, e.grade)) AS average_grade
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name;
