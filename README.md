# Social Media Backend API

A scalable GraphQL-based backend system for managing social media posts and user interactions, built as part of the ProDev Backend Engineering program.

## 📋 Table of Contents

- [Overview](#-overview)
- [ProDev Program Context](#-prodev-program-context)
- [Project Goals](#-project-goals)
- [Technologies Used](#-technologies-used)
- [Key Features](#-key-features)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Implementation Highlights](#-implementation-highlights)
- [Challenges & Solutions](#-challenges--solutions)
- [Best Practices & Takeaways](#-best-practices--takeaways)
- [Future Enhancements](#-future-enhancements)

## 🎯 Overview

This project is a backend system designed to power a social media feed with capabilities for post management, user interactions (likes, comments, shares), and flexible data querying through GraphQL. The system is built with scalability in mind, optimized for high-traffic scenarios typical of modern social platforms.

## 🎓 ProDev Program Context

This project was developed as part of the **ProDev Backend Engineering program**, which focuses on building production-ready backend systems using modern technologies and best practices.

### Program Learnings Applied

**Key Technologies:**
- Python & Django for robust backend development
- REST APIs & GraphQL for flexible data access patterns
- Docker for containerization and deployment consistency
- CI/CD pipelines for automated testing and deployment
- PostgreSQL for relational data management

**Backend Development Concepts:**
- **Database Design**: Normalized schema design for posts, users, and interactions with proper indexing strategies
- **Asynchronous Programming**: Handling concurrent user interactions efficiently
- **Caching Strategies**: Optimizing frequently accessed data (post feeds, user profiles)
- **API Design Patterns**: GraphQL schema design for flexible client requirements
- **Query Optimization**: N+1 query prevention and database performance tuning

## 🚀 Project Goals

1. **Post Management**: Design intuitive APIs for creating, fetching, updating, and managing social media posts
2. **Flexible Querying**: Implement GraphQL to enable clients to request exactly the data they need
3. **Scalability**: Optimize database schema and queries for high-volume user interactions
4. **Real-time Interactions**: Support likes, comments, and shares with efficient data structures
5. **Developer Experience**: Provide comprehensive API documentation and testing tools

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| **Django** | Backend framework for robust application structure |
| **PostgreSQL** | Relational database for data persistence |
| **Graphene-Django** | GraphQL integration for Django |
| **GraphQL Playground** | Interactive API testing and documentation |
| **Docker** | Containerization for consistent environments |
| **Git** | Version control with semantic commits |

## ✨ Key Features

### 1. GraphQL API Architecture
- **Flexible Queries**: Clients can request specific fields, reducing over-fetching
- **Type-Safe Schema**: Strongly typed API with automatic validation
- **Nested Queries**: Fetch posts with related comments and interactions in a single request
- **Mutations**: Create, update, and delete operations with proper authorization

### 2. Post Management System
```graphql
# Create a post
mutation {
  createPost(content: "Hello World!") {
    post {
      id
      content
      createdAt
      author {
        username
      }
    }
  }
}

# Create a reply (comment as a post)
mutation {
  createPost(content: "Great post!", parentPostId: 1) {
    post {
      id
      content
      parentPost {
        id
        content
      }
      author {
        username
      }
    }
  }
}

# Query posts with replies and interactions
query {
  posts(first: 10) {
    edges {
      node {
        id
        content
        likesCount
        repliesCount
        replies {
          id
          content
          author {
            username
          }
        }
      }
    }
  }
}
```

### 3. Interaction Management
- **Likes**: Track user likes with duplicate prevention
- **Shares**: Share tracking for analytics and reach metrics
- **Replies**: Threaded conversations using self-referential Post model
- **Follows**: User follow relationships with bidirectional queries
- **Activity Feed**: Aggregated view of user interactions and followed users' posts

### 4. Performance Optimization
- Database indexing on frequently queried fields
- Query batching to prevent N+1 problems using Django's `select_related` and `prefetch_related`
- Connection pooling for database efficiency
- Caching layer for popular posts and user feeds

## 🏁 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Docker (optional but recommended)

### Installation

1. **Clone the repository**
```bash
git clone git@github.com:shady-cj/alx-project-nexus.git
cd api
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp env.example .env
# Edit .env with your database credentials
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create a superuser**
  ```bash
  python manage.py createsuperuser
  ```

7. **Start the development server**
```bash
python manage.py runserver
```

8. **Access GraphQL Playground**
```
http://localhost:8000/graphql
```

### Docker Setup (Alternative)

```bash
docker-compose up --build
```

## 📚 API Documentation

### Core Models

<img width="2309" height="1627" alt="Social Media API" src="https://github.com/user-attachments/assets/bb649e4e-9f0b-4fd7-932d-33eb3661bc13" />




**User Model**
- `id`: Unique identifier
- `username`: Unique username
- `email`: User email address
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `profile`: Foreign key to user Profile 

**Profile Model**
- `id`: Unique identifier
- `first_name`: First name
- `last_name`: Last name
- `profile_photo`: Profile Photo
- `bio`: User bio
- `preferences`: set of user preferences.

**Post Model**
- `id`: Unique identifier
- `content`: Post text content
- `author`: Foreign key to User
- `parent_post`: Foreign key to Post (self-referential for replies/comments)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `is_published`: Boolean flag

**Follow Model**
- `user`: Foreign key to User (composite PK)
- `followed_by`: Foreign key to User (composite PK)
- `created_at`: Timestamp
- Note: Composite primary key on (user, followed_by)

**Interaction Model**
- `id`: Unique identifier
- `user`: Foreign key to User
- `post`: Foreign key to Post
- `type`: Enum (LIKE, SHARE, COMMENT)
- `created_at`: Timestamp

**Post Media Model**
- `id`: Unique identifier
- `post`: Foreign Key to Post
- `media_url`: URL field for attachment/media
- `type`: Enum (PHOTO, VIDEO, GIF)
- `created_at`: Timestamp

**Bookmark Model**
- `id`: Unique identifier
- `post`: Foreign key to post to bookmark
- `owner`: Owner of bookmark
- `bookmarked_on`: Date of bookmark

### Sample Queries & Mutations

View the full API documentation in the GraphQL Playground at `/graphql`

**Query all posts:**
```graphql
query {
  allPosts {
    edges {
      nodes {
        id
        content
        author {
          username
        }
        likes
        }
      }
  }
}
```

**Query all posts with pagination:**
```graphql
query {
  allPosts(first: 5) {
    pageInfo {
      hasNextPage
			hasPreviousPage
			startCursor
			endCursor
    }
    edges {
      nodes {
        id
        content
        author {
          username
        }
        likes
        }
      }
  }
}
```

**Create a comment:**
```graphql
mutation {
  createPost(content: "Great post!", parentPostId: 1) {
    post {
      id
      content
      parentPost {
        id
      }
      createdAt
    }
  }
}
```

**Follow a user:**
```graphql
mutation {
  followUser(usernameToFollow: "test") {
    success
    message
  }
}
```

**Get user's followers:**
```graphql
query {
  user(id: 1) {
    username
    followers {
      followedBy {
        username
      }
    }
    following {
      user {
        username
      }
    }
  }
}
```

**Like a post:**
```graphql
mutation {
  createInteraction(postId: 1, type: "LIKE") {
    success
    message
  }
}
```

## 💡 Implementation Highlights

### Git Commit Workflow
This project follows semantic commit conventions:

- `feat: set up Django project with PostgreSQL`
- `feat: create User and Post models with self-referential relationship`
- `feat: implement Follow model with composite primary key`
- `feat: create Interaction model for likes and shares`
- `feat: implement GraphQL API for querying posts, replies, and user interactions`
- `feat: add GraphQL mutations for following/unfollowing users`
- `feat: integrate and publish GraphQL Playground`
- `perf: optimize database queries for threaded posts and follower feeds`
- `docs: update README with API usage`

### Database Schema Design
- Self-referential Post model for threaded replies (Twitter/X-style conversations)
- Composite primary key on Follow model (user, followed_by) for efficient relationship queries
- Proper foreign key relationships between Users, Posts, Follows, and Interactions
- Composite unique constraints to prevent duplicate interactions
- Strategic indexing on `created_at`, foreign key fields, and follow relationships
- Normalized structure to minimize data redundancy

### Query Optimization Strategies
- Used `select_related()` for one-to-one and foreign key relationships
- Applied `prefetch_related()` for many-to-many and reverse foreign key queries
- Implemented database-level aggregation for counts (likes, comments)
- Added pagination to prevent memory issues with large datasets

## 🔧 Challenges & Solutions

### Challenge 1: N+1 Query Problem
**Problem**: Initial implementation caused hundreds of database queries when fetching posts with related data.

**Solution**: 
- Implemented Django's `select_related` and `prefetch_related` in GraphQL resolvers
- Used Graphene's optimization features for nested queries
- Result: Reduced query count from 500+ to under 10 for typical feed requests

### Challenge 2: Duplicate Follow Prevention
**Problem**: Users could follow the same person multiple times, creating data inconsistency.

**Solution**:
- Used composite primary key on Follow model `(user, followed_by)` at database level
- Eliminated need for separate id field, making the relationship naturally unique
- Implemented idempotent follow/unfollow mutations
- Return meaningful messages for already-existing relationships

### Challenge 3: Threaded Post Queries
**Problem**: Fetching nested replies efficiently without causing performance issues or infinite recursion.

**Solution**:
- Implemented depth limiting for recursive post queries (max 3 levels of replies)
- Used Django's `select_related('parent_post')` for efficient parent lookups
- Created separate resolvers for reply counts vs fetching full reply trees
- Added pagination for replies to prevent loading thousands of nested posts

### Challenge 4: Follow Feed Performance
**Problem**: Generating personalized feeds from followed users required complex joins and was slow at scale.

**Solution**:
- Denormalized follow counts on User model for fast profile displays
- Implemented database-level indexing on Follow model's composite key
- Used `prefetch_related` for batch-loading followed users' posts
- Considered future fan-out approach for high-volume users

## 📖 Best Practices & Takeaways

### Technical Best Practices
1. **Type Safety**: GraphQL's strongly-typed schema caught errors at development time
2. **API Versioning**: GraphQL eliminates versioning concerns through schema evolution
3. **Error Handling**: Implemented consistent error response format across all mutations
4. **Testing**: Created comprehensive test suite covering queries, mutations, and edge cases
5. **Documentation**: Self-documenting API through GraphQL's introspection

### Personal Takeaways
- **GraphQL vs REST**: GraphQL significantly reduces over-fetching and under-fetching compared to traditional REST APIs
- **Schema-First Design**: Designing the GraphQL schema before implementation led to cleaner, more maintainable code
- **Database Optimization**: Understanding query patterns early is crucial for scalability
- **Developer Experience**: GraphQL Playground dramatically improves API testing and documentation
- **Real-World Complexity**: Building even a "simple" social feed involves nuanced decisions around data modeling, performance, and user experience

### Skills Developed
- Advanced Django ORM usage and query optimization
- GraphQL schema design and resolver implementation
- Database indexing and performance tuning
- Scalable backend architecture patterns
- API documentation and developer tooling

## 🔮 Future Enhancements

- [ ] Real-time subscriptions using GraphQL WebSockets
- [ ] Redis caching layer for hot data
- [ ] Full-text search using PostgreSQL or Elasticsearch
- [ ] Rate limiting and abuse prevention
- [ ] Image upload and media management
- [ ] Notification system for interactions
- [ ] Comprehensive monitoring and logging

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or feedback about this project:
- Email: petersp2000@gmail.com
- GitHub: [@shady-cj](https://github.com/shady-cj)

---

**Built with ❤️ as part of the ProDev Backend Engineering Program**
