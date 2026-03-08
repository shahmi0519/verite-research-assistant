from memory_store import LongTermMemoryStore

store = LongTermMemoryStore()

# Simulate saving 3 exchanges for a user
store.append("user_123", "What is forced labour?", "Forced labour refers to...")
store.append("user_123", "What does Verité say about it?", "Verité's research shows...")
store.append("user_123", "Thanks!", "You're welcome!")

# Now retrieve context for that user
context = store.get_summary("user_123")
print(context)

# A different user should have no context
empty = store.get_summary("user_456")
print(f"\nNew user context: '{empty}'")