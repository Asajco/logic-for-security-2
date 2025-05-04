from marketplace import BookMarketplace

def main():
    # Create marketplace instance
    marketplace = BookMarketplace()
    
    # Add some sample data
    print("Setting up test data...")
    
    # Add customers
    marketplace.db.customers = {
        1: {"name": "Alice Smith", "address": "123 Main St, Copenhagen", "opt_in_marketing": True},
        2: {"name": "Bob Johnson", "address": "456 Oak Ave, Copenhagen", "opt_in_marketing": False}
    }
    
    # Add vendors
    marketplace.db.vendors = {
        1: {"name": "Book Haven"},
        2: {"name": "Academic Press"}
    }
    
    # Test offer handler
    print("\nTesting offer handler...")
    book_info = {
        "title": "Python Programming for Beginners",
        "author": "Jane Doe",
        "year": 2024,
        "edition": "3rd",
        "publisher": "Tech Books",
        "condition": "new",
        "description": "A comprehensive guide to Python programming",
        "price": 29.99
    }
    
    result = marketplace.offer_handler(1, book_info)
    print(f"Offer result: {result}")
    
    book_info2 = {
        "title": "History of Denmark",
        "author": "Hans Jensen",
        "year": 2023,
        "edition": "1st",
        "publisher": "Nordic Press",
        "condition": "used",
        "description": "A detailed history of Denmark from Vikings to modern day",
        "price": 19.99
    }
    
    result = marketplace.offer_handler(2, book_info2)
    print(f"Offer result: {result}")
    
    # Test search handler
    print("\nTesting search handler...")
    search_result = marketplace.search_handler("python")
    print(f"Search for 'python': {search_result}")
    
    search_result = marketplace.search_handler("history")
    print(f"Search for 'history': {search_result}")
    
    # Test purchase handler
    print("\nTesting purchase handler...")
    purchase_result = marketplace.purchase_handler(1, 1, 29.99)
    print(f"Purchase result success: {purchase_result['success']}")
    print(f"Vendor confirmation: {purchase_result['vendor_confirmation']}")
    print(f"Customer confirmation: {purchase_result['customer_confirmation']}")
    
    # Try to purchase an already sold book
    print("\nTesting purchase of already sold book...")
    purchase_result = marketplace.purchase_handler(2, 1, 29.99)
    print(f"Purchase result: {purchase_result}")
    
    # Check database status
    print("\nFinal database state:")
    print(f"Available books: {[offer_id for offer_id, offer in marketplace.db.book_offers.items() if offer['available']]}")
    print(f"Purchases: {marketplace.db.purchases}")

if __name__ == "__main__":
    main()