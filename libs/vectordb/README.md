# Vector DB for Parrot

## Usage

### Create the Collection Model Class

```python
class HeroModel(CollectionModel):
  __collection_name__ = "hero"

  id: int | None = Field(default=None, primary_key=True)
  name: str
  secret_name: str
  age: int | None = None

db = AsyncMilvusDb("database.db")
await setup_milvus(db)
```

### Insert entities

```python
hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
await db.insert(Hero).values([hero_1, hero_2]).exec()
```

### Update an entity

```python
hero_3 = Hero(name="Deadpond", secret_name="Wive Wilson")
await db.update(Hero).set(hero).where(eq(Hero.name, "Deadpond")).exec()
```

### Delete an entity

```python
await db.delete(Hero).where(eq(Hero.name, "Deadpond")).exec()
```

### Query entities

```python
await db.query(Hero).order_by(Hero.name).limit(10).offset(10).exec()
```
