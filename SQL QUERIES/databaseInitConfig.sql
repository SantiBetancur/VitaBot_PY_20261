-- UUIDs
create extension if not exists "uuid-ossp";

-- Vector embeddings
create extension if not exists vector;

create schema if not exists rag;
create schema if not exists app;

create table rag.documents (
    id uuid primary key default uuid_generate_v4(),
    
    content text not null,
    
    -- Ajusta la dimensión según el modelo (ej: 1536 para text-embedding-3-small)
    embedding vector(1536) not null,
    
    source text,
    chunk_index int,
    
    metadata jsonb,
    
    embedding_model text default 'text-embedding-3-small',
    version int default 1,
    
    created_at timestamp with time zone default now()
);

-- IVFFLAT (buena opción inicial)
create index documents_embedding_idx
on rag.documents
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Importante: después de insertar datos masivos, ejecuta:
analyze rag.documents;

create index documents_source_idx on rag.documents(source);
create index documents_metadata_idx on rag.documents using gin(metadata);




create table app.users (
    id uuid primary key default uuid_generate_v4(),
    
    external_id text unique, -- id de Zoho o usuario sin login
    
    created_at timestamp with time zone default now()
);


create table app.sessions (
    id uuid primary key default uuid_generate_v4(),
    
    user_id uuid references app.users(id) on delete cascade,
    
    created_at timestamp with time zone default now(),
    last_activity timestamp with time zone default now()
);

create table app.messages (
    id uuid primary key default uuid_generate_v4(),
    
    session_id uuid references app.sessions(id) on delete cascade,
    
    role text check (role in ('user', 'assistant')) not null,
    
    content text not null,
    
    -- Referencias a documentos usados en RAG
    sources jsonb,
    
    created_at timestamp with time zone default now()
);

create index messages_session_idx on app.messages(session_id);
create index messages_created_at_idx on app.messages(created_at);

create index sessions_user_idx on app.sessions(user_id);


alter table app.users enable row level security;
alter table app.sessions enable row level security;
alter table app.messages enable row level security;

