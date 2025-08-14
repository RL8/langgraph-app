# Backend Upgrade Plan: Music App Implementation

## Overview
This document outlines the complete backend upgrade plan to transform the current LangGraph data enrichment app into a music discovery platform with MCP integration, Supabase database, and CopilotKit-ready APIs.

## Current State → Target State

| Component | Current | Target | Upgrade Required |
|-----------|---------|--------|------------------|
| **Database** | None | Supabase PostgreSQL | ✅ Full schema migration |
| **External Data** | Direct API calls | MCP servers | ✅ MCP implementation |
| **Workflows** | Single research graph | Multiple specialized graphs | ✅ New workflow creation |
| **API Layer** | CLI only | FastAPI endpoints | ✅ API development |
| **State Management** | Ephemeral | Persistent user data | ✅ User session handling |

## Phase 1: Database Foundation (Week 1)

### 1.1 Supabase Schema Migration
**Timeline**: Days 1-3
**Dependencies**: Existing Supabase account

**Tasks**:
- [ ] Execute database migration scripts from `database_migration_plan.md`
- [ ] Create all core tables (artists, albums, songs, curated_sources)
- [ ] Create user data tables (profiles, rankings, selections, reviews)
- [ ] Create trivia tables (questions, sessions, answers, leaderboard)
- [ ] Create onboarding tables (tour progress, preferences)
- [ ] Add all required indexes for performance
- [ ] Test data integrity and relationships

**Deliverables**:
- Complete Supabase schema
- Migration validation report
- Performance benchmarks

### 1.2 Database Integration Layer
**Timeline**: Days 4-5
**Dependencies**: Schema migration complete

**Tasks**:
- [ ] Set up Supabase client in existing app
- [ ] Create database access layer (DAL)
- [ ] Implement connection pooling
- [ ] Add error handling and retry logic
- [ ] Create database utilities for common operations
- [ ] Add database migration scripts to project

**Deliverables**:
- Database connection layer
- Common query utilities
- Error handling framework

## Phase 2: MCP Server Implementation (Week 2)

### 2.1 MCP Server Architecture
**Timeline**: Days 1-2
**Dependencies**: None

**Tasks**:
- [ ] Create MCP server directory structure
- [ ] Set up MCP protocol implementation
- [ ] Create shared utilities for MCP servers
- [ ] Implement MCP server base classes
- [ ] Add configuration management for MCPs
- [ ] Create MCP server testing framework

**Deliverables**:
- MCP server foundation
- Base classes and utilities
- Testing framework

### 2.2 Artist Search MCP
**Timeline**: Days 3-4
**Dependencies**: MCP foundation

**Tasks**:
- [ ] Implement `artist_search` MCP server
- [ ] Integrate Wikidata SPARQL queries
- [ ] Add result caching and rate limiting
- [ ] Implement error handling and fallbacks
- [ ] Add result validation and filtering
- [ ] Create comprehensive tests

**Deliverables**:
- Working artist search MCP
- Wikidata integration
- Caching and rate limiting

### 2.3 Artist Indexing MCP
**Timeline**: Days 5-7
**Dependencies**: Artist search MCP

**Tasks**:
- [ ] Implement `artist_index` MCP server
- [ ] Integrate MediaWiki API for Wikipedia search
- [ ] Add Google Custom Search Engine integration
- [ ] Implement reference extraction and filtering
- [ ] Add confidence scoring and validation
- [ ] Create comprehensive tests

**Deliverables**:
- Working artist indexing MCP
- Wikipedia and web search integration
- Reference curation system

## Phase 3: Workflow Implementation (Week 3)

### 3.1 Indexing Workflow
**Timeline**: Days 1-3
**Dependencies**: MCP servers, database layer

**Tasks**:
- [ ] Create `indexing_graph.py` for artist indexing
- [ ] Implement workflow nodes:
  - [ ] Check artist indexed status
  - [ ] Search Wikipedia pages
  - [ ] Extract references
  - [ ] Fallback web search
  - [ ] Store curated sources
  - [ ] Process albums and songs
- [ ] Add MCP integration points
- [ ] Implement progress tracking
- [ ] Add error handling and recovery
- [ ] Create comprehensive tests

**Deliverables**:
- Complete indexing workflow
- MCP integration
- Progress tracking system

### 3.2 Trivia Workflow
**Timeline**: Days 4-5
**Dependencies**: Indexing workflow, database layer

**Tasks**:
- [ ] Create `trivia_graph.py` for trivia generation
- [ ] Implement workflow nodes:
  - [ ] Load curated sources
  - [ ] Generate questions
  - [ ] Validate answers
  - [ ] Track scores
  - [ ] Update leaderboard
- [ ] Add LLM integration for question generation
- [ ] Implement difficulty calibration
- [ ] Add session management
- [ ] Create comprehensive tests

**Deliverables**:
- Complete trivia workflow
- LLM integration
- Session management

### 3.3 Workflow Orchestration
**Timeline**: Days 6-7
**Dependencies**: Both workflows

**Tasks**:
- [ ] Create workflow registry and management
- [ ] Implement job queuing and scheduling
- [ ] Add workflow monitoring and logging
- [ ] Create workflow status endpoints
- [ ] Implement workflow recovery mechanisms
- [ ] Add performance optimization

**Deliverables**:
- Workflow orchestration system
- Job management
- Monitoring and logging

## Phase 4: API Layer Development (Week 4)

### 4.1 FastAPI Foundation
**Timeline**: Days 1-2
**Dependencies**: Database layer, MCP servers

**Tasks**:
- [ ] Set up FastAPI application structure
- [ ] Create API router organization
- [ ] Implement authentication and authorization
- [ ] Add request/response models
- [ ] Create API documentation
- [ ] Add error handling middleware
- [ ] Implement rate limiting

**Deliverables**:
- FastAPI application foundation
- Authentication system
- API documentation

### 4.2 Core API Endpoints
**Timeline**: Days 3-5
**Dependencies**: FastAPI foundation

**Tasks**:
- [ ] Implement artist search endpoint (`/api/artists/search`)
- [ ] Implement artist indexing endpoint (`/api/artists/{id}/index`)
- [ ] Implement album listing endpoint (`/api/artists/{id}/albums`)
- [ ] Implement user profile endpoints (`/api/user/profile`)
- [ ] Implement album ranking endpoints (`/api/user/album-rankings`)
- [ ] Implement song selection endpoints (`/api/user/song-selections`)
- [ ] Implement trivia endpoints (`/api/trivia/generate`, `/api/trivia/submit`)
- [ ] Add comprehensive input validation
- [ ] Implement response caching

**Deliverables**:
- Complete API endpoint set
- Input validation
- Response caching

### 4.3 API Integration Testing
**Timeline**: Days 6-7
**Dependencies**: All API endpoints

**Tasks**:
- [ ] Create comprehensive API tests
- [ ] Test all endpoint combinations
- [ ] Test error scenarios and edge cases
- [ ] Performance testing under load
- [ ] Security testing
- [ ] API documentation updates

**Deliverables**:
- Complete API test suite
- Performance benchmarks
- Security validation

## Phase 5: Integration & Testing (Week 5)

### 5.1 End-to-End Integration
**Timeline**: Days 1-3
**Dependencies**: All components

**Tasks**:
- [ ] Integrate all components (MCPs, workflows, APIs, database)
- [ ] Test complete user workflows
- [ ] Validate data flow between components
- [ ] Test error handling across components
- [ ] Performance optimization
- [ ] Load testing

**Deliverables**:
- Fully integrated system
- End-to-end test results
- Performance optimization

### 5.2 Production Readiness
**Timeline**: Days 4-5
**Dependencies**: Integration complete

**Tasks**:
- [ ] Production environment setup
- [ ] Monitoring and alerting configuration
- [ ] Logging and observability setup
- [ ] Backup and recovery procedures
- [ ] Security hardening
- [ ] Documentation completion

**Deliverables**:
- Production-ready system
- Monitoring and alerting
- Complete documentation

### 5.3 Deployment & Validation
**Timeline**: Days 6-7
**Dependencies**: Production readiness

**Tasks**:
- [ ] Deploy to production environment
- [ ] Validate all functionality in production
- [ ] Monitor system performance
- [ ] User acceptance testing
- [ ] Bug fixes and optimizations
- [ ] Go-live preparation

**Deliverables**:
- Production deployment
- System validation
- Go-live readiness

## MCP Integration Summary

| MCP Server | Purpose | External Dependencies | Integration Points |
|------------|---------|----------------------|-------------------|
| `artist_search` | Wikidata artist discovery | Wikidata SPARQL | FastAPI `/api/artists/search` |
| `artist_index` | Wikipedia + web indexing | MediaWiki API, Google CSE | LangGraph indexing workflow |

## Workflow Integration Summary

| Workflow | Purpose | MCP Usage | API Endpoints |
|----------|---------|-----------|---------------|
| `indexing_graph` | Artist/album/song indexing | `artist_index` | `/api/artists/{id}/index` |
| `trivia_graph` | Question generation & scoring | None (internal LLM) | `/api/trivia/generate`, `/api/trivia/submit` |

## API Endpoint Summary

| Endpoint | Method | Purpose | MCP Usage |
|----------|--------|---------|-----------|
| `/api/artists/search` | POST | Artist discovery | `artist_search` |
| `/api/artists/{id}/index` | POST | Trigger indexing | `artist_index` (via workflow) |
| `/api/artists/{id}/albums` | GET | Get albums | None (database) |
| `/api/user/profile` | GET/PUT | User profile | None (database) |
| `/api/user/album-rankings` | POST | Save rankings | None (database) |
| `/api/user/song-selections` | POST | Save selections | None (database) |
| `/api/trivia/generate` | POST | Generate questions | None (workflow) |
| `/api/trivia/submit` | POST | Submit answers | None (workflow) |

## Success Criteria

### Technical Criteria
- [ ] All MCP servers operational and tested
- [ ] All workflows functional and optimized
- [ ] All API endpoints working and documented
- [ ] Database schema complete and optimized
- [ ] System performance meets requirements
- [ ] Error handling comprehensive and tested

### Functional Criteria
- [ ] Artist search returns accurate results
- [ ] Indexing workflow completes successfully
- [ ] Album ranking system operational
- [ ] Trivia generation produces quality questions
- [ ] User data persistence working correctly
- [ ] API responses meet frontend requirements

## Timeline Summary

| Week | Phase | Duration | Key Deliverables |
|------|-------|----------|------------------|
| 1 | Database Foundation | 5 days | Complete Supabase schema |
| 2 | MCP Implementation | 7 days | Artist search & indexing MCPs |
| 3 | Workflow Development | 7 days | Indexing & trivia workflows |
| 4 | API Development | 7 days | Complete API layer |
| 5 | Integration & Testing | 7 days | Production-ready system |

**Total Timeline**: 5 weeks
**Risk Level**: Medium (complex integration)
**Dependencies**: Supabase account, external API access
**Team Size**: 1-2 developers recommended



