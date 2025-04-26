CREATE TABLE IF NOT EXISTS meetings (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    attendees_accepted INTEGER,
    attendees_accepted_emails TEXT[],
    attendees_tentative INTEGER,
    attendees_declined INTEGER,
    attendees_emails TEXT[],
    attendees_needs_action INTEGER,
    summary TEXT,
    user_email VARCHAR(255) NOT NULL,
    division VARCHAR(255),
    department VARCHAR(255),
    subdepartment VARCHAR(255),
    unique_departments INTEGER,
    departments_list TEXT[],
    meeting_size_category VARCHAR(50),
    is_one_on_one BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- indexes
CREATE INDEX IF NOT EXISTS idx_meetings_user_email ON meetings(user_email);
CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
CREATE INDEX IF NOT EXISTS idx_meetings_department ON meetings(department); 