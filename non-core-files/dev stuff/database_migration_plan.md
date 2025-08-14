# Database Migration Plan: Music App Schema

## Overview
This document outlines the migration plan to update the existing Supabase schema to support the dual-pane music discovery app with CopilotKit chat interface and React dashboard.

## Target Schema Requirements

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `artists` | Artist metadata | `id, name, qid, country, birth_year, image_url, is_indexed, created_at` |
| `albums` | Album catalog | `id, artist_id, name, release_year, total_tracks, image_url, created_at` |
| `songs` | Song details | `id, album_id, name, track_number, duration, created_at` |
| `curated_sources` | Indexed sources | `id, entity_id, entity_type, url, context_snippet, source_type, confidence, created_at` |

### User Data Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `user_profiles` | User data | `user_id, name, created_at, last_active` |
| `user_album_rankings` | Album rankings | `id, user_id, album_id, rank_position, created_at` |
| `user_song_selections` | Song favorites | `id, user_id, song_id, album_id, is_favorite, created_at` |
| `user_album_reviews` | Album reviews | `id, user_id, album_id, review_text, rating, created_at` |
| `user_song_notes` | Song notes | `id, user_id, song_id, note_text, created_at` |

### Trivia & Gameplay Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `trivia_questions` | Question bank | `id, artist_id, album_id, question_text, options, correct_answer, difficulty, source_url, created_at` |
| `trivia_sessions` | Game sessions | `id, user_id, artist_id, album_id, score, total_questions, completed_at, created_at` |
| `trivia_answers` | Individual answers | `id, session_id, question_id, user_answer, is_correct, response_time, created_at` |
| `leaderboard` | Scores | `id, user_id, artist_id, album_id, score, percentage, rank_position, created_at` |

### Induction/Tour Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `user_onboarding` | Tour progress | `id, user_id, step_completed, tour_data, completed_at, created_at` |
| `user_preferences` | App preferences | `id, user_id, preference_key, preference_value, created_at` |

## Migration Strategy Options

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A. Modify Existing** | Update current tables to match new schema | Preserves existing data, simpler | May break existing functionality |
| **B. Parallel Migration** | Create new tables alongside existing | No downtime, safe rollback | More complex, temporary duplication |
| **C. Fresh Start** | Drop and recreate schema | Clean slate, optimal design | Loses all existing data |

## Action Plan

### Phase 1: Schema Analysis (Day 1)
**Tasks:**
1. Connect to Supabase and examine current schema
2. Document existing tables, relationships, and constraints
3. Identify reusable components vs. new requirements
4. Compare current schema with target schema
5. Determine which migration strategy to use

**Deliverables:**
- Current schema documentation
- Gap analysis report
- Migration strategy recommendation

### Phase 2: Migration Scripts (Day 2-3)
**Tasks:**
1. Create SQL migration scripts for each table
2. Include data transformation logic if needed
3. Add proper indexes and constraints
4. Create rollback scripts for each migration
5. Test scripts on development database

**Deliverables:**
- Complete migration SQL scripts
- Rollback scripts
- Index creation scripts
- Data transformation scripts (if needed)

### Phase 3: Testing (Day 4)
**Tasks:**
1. Execute migrations on development database
2. Verify data integrity and relationships
3. Test application functionality
4. Performance testing with sample data
5. Validate all foreign key relationships

**Deliverables:**
- Test results report
- Performance benchmarks
- Bug fixes and script updates

### Phase 4: Production Deployment (Day 5)
**Tasks:**
1. Schedule migration during low-traffic period
2. Execute migrations in production
3. Monitor for any issues
4. Verify application functionality
5. Update application code to use new schema

**Deliverables:**
- Production migration completion
- Monitoring dashboard setup
- Application updates deployed

## Required SQL Scripts

### Core Table Creation
```sql
-- Artists table
CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    qid VARCHAR(50), -- Wikidata QID
    country VARCHAR(100),
    birth_year INTEGER,
    image_url TEXT,
    is_indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Albums table
CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    release_year INTEGER,
    total_tracks INTEGER,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Songs table
CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    track_number INTEGER,
    duration INTEGER, -- in seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Curated sources table (polymorphic)
CREATE TYPE entity_type_enum AS ENUM ('artist', 'album', 'song');
CREATE TABLE IF NOT EXISTS curated_sources (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL,
    entity_type entity_type_enum NOT NULL,
    url TEXT NOT NULL,
    context_snippet TEXT,
    source_type VARCHAR(50),
    confidence DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### User Data Tables
```sql
-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    user_preferences JSONB DEFAULT '{}',
    favorite_genres JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User album rankings
CREATE TABLE IF NOT EXISTS user_album_rankings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
    rank_position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, album_id)
);

-- User song selections
CREATE TABLE IF NOT EXISTS user_song_selections (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, song_id)
);
```

### Trivia Tables
```sql
-- Trivia questions
CREATE TABLE IF NOT EXISTS trivia_questions (
    id SERIAL PRIMARY KEY,
    artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL, -- Array of 4 options
    correct_answer VARCHAR(10) NOT NULL, -- A, B, C, or D
    difficulty VARCHAR(20) DEFAULT 'medium',
    source_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trivia sessions
CREATE TABLE IF NOT EXISTS trivia_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
-- Search and filtering indexes
CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name);
CREATE INDEX IF NOT EXISTS idx_albums_artist_id ON albums(artist_id);
CREATE INDEX IF NOT EXISTS idx_songs_album_id ON songs(album_id);
CREATE INDEX IF NOT EXISTS idx_curated_sources_entity ON curated_sources(entity_id, entity_type);

-- User data indexes
CREATE INDEX IF NOT EXISTS idx_user_rankings_user_id ON user_album_rankings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_selections_user_id ON user_song_selections(user_id);
CREATE INDEX IF NOT EXISTS idx_trivia_sessions_user_id ON trivia_sessions(user_id);

-- Leaderboard indexes
CREATE INDEX IF NOT EXISTS idx_trivia_sessions_album_score ON trivia_sessions(album_id, score DESC);
```

## Rollback Plan

### If Migration Fails
1. **Immediate rollback** using rollback scripts
2. **Data recovery** from backups if needed
3. **Investigation** of failure cause
4. **Fix and retry** migration

### Rollback Scripts
```sql
-- Drop tables in reverse order
DROP TABLE IF EXISTS trivia_sessions CASCADE;
DROP TABLE IF EXISTS trivia_questions CASCADE;
DROP TABLE IF EXISTS user_song_selections CASCADE;
DROP TABLE IF EXISTS user_album_rankings CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS curated_sources CASCADE;
DROP TABLE IF EXISTS songs CASCADE;
DROP TABLE IF EXISTS albums CASCADE;
DROP TABLE IF EXISTS artists CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS entity_type_enum CASCADE;
```

## Success Criteria

### Technical Criteria
- [ ] All tables created successfully
- [ ] All foreign key relationships working
- [ ] All indexes created and optimized
- [ ] Application can connect and query new schema
- [ ] No data loss during migration

### Functional Criteria
- [ ] Artist search functionality works
- [ ] Album ranking system operational
- [ ] Song selection working
- [ ] Trivia game functional
- [ ] User profiles accessible
- [ ] Dashboard displays correctly

## Timeline Summary

| Day | Phase | Duration | Key Activities |
|-----|-------|----------|----------------|
| 1 | Analysis | 1 day | Schema review, gap analysis |
| 2-3 | Scripts | 2 days | Migration script creation |
| 4 | Testing | 1 day | Development testing |
| 5 | Deployment | 1 day | Production migration |

**Total Timeline**: 5 days
**Risk Level**: Medium (depends on existing data complexity)
**Rollback Time**: 30 minutes (if needed)



