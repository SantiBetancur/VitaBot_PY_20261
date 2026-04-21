select
    id,
    content,
    source,
    metadata,
    1 - (embedding <=> '[VECTOR_AQUI]') as similarity
from rag.documents
order by embedding <=> '[VECTOR_AQUI]'
limit 5;