# Cypher Cookbook (for self-hosters)

If you run your own copy of the graph, these are read-only queries behind the gateway
tools — handy for exploration or building your own tools. The hosted gateway does **not**
accept raw Cypher; this is for direct Neo4j access to your own instance.

> Set the database to read-only first: `ALTER DATABASE neo4j SET ACCESS READ ONLY;`

### Semantic passage search (what `search_corpus` runs)
```cypher
CALL db.index.vector.queryNodes('semantic_unit_embeddings', 8, $embedding)
YIELD node AS su, score AS similarity
WHERE similarity > 0.40
MATCH (su)-[:BELONGS_TO]->(t:Text)
RETURN su.canonical_ref AS ref, t.title AS text, su.english_text AS en, similarity
ORDER BY similarity DESC;
```
`$embedding` is a 1024-d BGE-M3 vector of the query (the gateway computes it via DeepInfra).

### Exact passage by reference
```cypher
MATCH (tu:TextUnit) WHERE toLower(tu.canonical_id) = 'bavli-berakhot_5_1'
MATCH (tu)-[:BELONGS_TO]->(t:Text)
RETURN tu.hebrew_text, tu.english_text, t.title;
```

### Concept neighborhood (typed relations)
```cypher
MATCH (c:CanonicalConcept {canonical_id:'cluster_15840'})-[r:CANONICAL_REL]-(nbr:CanonicalConcept)
WITH nbr, coalesce(r.relationship_type, r.type) AS rel_type, r.confidence AS conf
RETURN rel_type, nbr.name, conf ORDER BY conf DESC LIMIT 20;
```

### Prerequisite DAG (learning order)
```cypher
MATCH (p:CanonicalConcept)-[:PREREQUISITE]->(c:CanonicalConcept {canonical_id:'cluster_15840'})
RETURN p.name, p.difficulty;             // study these first
```

### The thematic map
```cypher
MATCH (g:Galaxy) RETURN g.name, g.great_question, g.constellation_count ORDER BY g.galaxy_id;
MATCH (c:CanonicalConcept)-[:IN_CONSTELLATION]->(con:Constellation {constellation_id:$id})
RETURN c.name, c.difficulty ORDER BY c.is_keystone DESC;
```

### Commentaries on a base text
```cypher
MATCH (comm:TextUnit)-[r:CONNECTS_TO {kind:'comments_on'}]->(b:TextUnit)
WHERE r.base_text_slug = 'bavli-berakhot'
MATCH (comm)-[:BELONGS_TO]->(t:Text)
RETURN DISTINCT t.title, comm.english_text LIMIT 20;
```

### Entities in a passage
```cypher
MATCH (su:SemanticUnit {su_id:$su_id})<-[m:MENTIONED_IN]-(e:Entity)
RETURN e.entity_type, e.name, e.description ORDER BY m.importance DESC;
```

See [schema.md](./schema.md) for the full label/relationship/property inventory.
