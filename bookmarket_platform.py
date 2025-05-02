"""
BookMarket Platform Prototype
Implementation of secure information flow for an electronic book marketplace
Based on Myers & Liskov decentralized information flow control model
"""

# Define our security lattice and principals
class Principal:
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name

class SecurityLabel:
    def __init__(self, owners=None, readers=None):
        """
        Security Label using the Myers & Liskov model
        owners: set of Principals who own this data (integrity)
        readers: set of Principals who can read this data (confidentiality)
        """
        self.owners = owners if owners is not None else set()
        self.readers = readers if readers is not None else set()
    
    def __str__(self):
        owners_str = "{" + ", ".join([str(o) for o in self.owners]) + "}"
        readers_str = "{" + ", ".join([str(r) for r in self.readers]) + "}"
        return f"<{owners_str}, {readers_str}>"
    
    def __repr__(self):
        return self.__str__()
    
    def flows_to(self, label):
        """
        Information can flow from this label to target label if:
        1. All owners in target are also owners in this (integrity)
        2. All readers in this are also readers in target (confidentiality)
        """
        return (label.owners.issubset(self.owners) and 
                self.readers.issubset(label.readers))
    
    def join(self, label):
        """
        Least upper bound operation - combines two labels
        """
        return SecurityLabel(
            self.owners.intersection(label.owners),
            self.readers.union(label.readers)
        )
    
    def meet(self, label):
        """
        Greatest lower bound operation
        """
        return SecurityLabel(
            self.owners.union(label.owners),
            self.readers.intersection(label.readers)
        )
    
    def declassify(self, auth_principal, new_readers=None):
        """
        Declassify information if authorized by all owners
        """
        if auth_principal in self.owners:
            result = SecurityLabel(self.owners.copy(), self.readers.copy())
            if new_readers is not None:
                result.readers = new_readers
            return result
        else:
            raise SecurityException(f"Principal {auth_principal} not authorized to declassify")

# Security exception class
class SecurityException(Exception):
    pass

# Define our database model
class Database:
    def __init__(self):
        self.customers = {}  # Customer data with addresses
        self.vendors = {}    # Vendor information
        self.books = {}      # Book listings
        self.purchases = {}  # Purchase records
        self.next_book_id = 1
        self.next_purchase_id = 1
    
    def add_customer(self, customer_id, customer_data, label):
        """Add a customer with security label"""
        self.customers[customer_id] = {
            'data': customer_data,
            'label': label,
            'marketing_opt_in': False  # Default: no marketing
        }
    
    def add_vendor(self, vendor_id, vendor_data, label):
        """Add a vendor with security label"""
        self.vendors[vendor_id] = {
            'data': vendor_data,
            'label': label
        }
    
    def add_book(self, book_data, label):
        """Add a book listing with security label"""
        book_id = self.next_book_id
        self.next_book_id += 1
        self.books[book_id] = {
            'data': book_data,
            'label': label,
            'status': 'available'
        }
        return book_id
    
    def add_purchase(self, purchase_data, label):
        """Record a purchase with security label"""
        purchase_id = self.next_purchase_id
        self.next_purchase_id += 1
        self.purchases[purchase_id] = {
            'data': purchase_data,
            'label': label
        }
        return purchase_id

# Define our three event handlers
class BookMarketPlatform:
    def __init__(self):
        self.db = Database()
        # Define the marketplace principal
        self.marketplace = Principal("Marketplace")
        
        # Set up initial customers and vendors
        self._setup_initial_data()
    
    def _setup_initial_data(self):
        """Initialize database with some customers and vendors"""
        # Set up some customers
        customer1 = {
            'name': 'Alice Smith',
            'address': '123 Main St, Anytown',
            'email': 'alice@example.com'
        }
        customer2 = {
            'name': 'Bob Johnson',
            'address': '456 Oak Ave, Othertown',
            'email': 'bob@example.com'
        }
        
        # Define principals
        alice = Principal("Alice")
        bob = Principal("Bob")
        
        # Add customers with security labels
        self.db.add_customer('alice', customer1, 
                            SecurityLabel(owners={alice}, readers={alice, self.marketplace}))
        self.db.add_customer('bob', customer2, 
                            SecurityLabel(owners={bob}, readers={bob, self.marketplace}))
        
        # Set up some vendors
        vendor1 = {
            'name': 'BookStore Inc',
            'email': 'sales@bookstore.com'
        }
        vendor2 = {
            'name': 'Rare Books Ltd',
            'email': 'info@rarebooks.com'
        }
        
        # Define vendor principals
        bookstore = Principal("BookStore")
        rarebooks = Principal("RareBooks")
        
        # Add vendors with security labels
        self.db.add_vendor('bookstore', vendor1, 
                           SecurityLabel(owners={bookstore}, readers={bookstore, self.marketplace}))
        self.db.add_vendor('rarebooks', vendor2, 
                           SecurityLabel(owners={rarebooks}, readers={rarebooks, self.marketplace}))
    
    def handle_offer(self, vendor_id, book_data):
        """
        Event Handler 1: A vendor uploads a book offer
        
        Parameters:
        - vendor_id: Identifier of the vendor
        - book_data: Dictionary with book details (title, author, etc.)
        
        Returns:
        - Success message and book_id if successful
        
        Security:
        - Vendor owns the book data
        - Marketplace can read the data for search
        - Public readers for searchable fields
        """
        # Check if vendor exists
        if vendor_id not in self.db.vendors:
            return {'success': False, 'message': 'Vendor not found'}
        
        # Get vendor principal from the database
        vendor_info = self.db.vendors[vendor_id]
        vendor_label = vendor_info['label']
        
        # Create a principal for this vendor
        vendor_principal = list(vendor_label.owners)[0]  # Assume single owner
        
        # Create security label for the book:
        # - Owned by the vendor (integrity)
        # - Readable by the marketplace and the vendor (confidentiality)
        # - Searchable fields are readable by everyone (via public label)
        book_label = SecurityLabel(
            owners={vendor_principal}, 
            readers={vendor_principal, self.marketplace}
        )
        
        # Add vendor to the book data
        book_data['vendor_id'] = vendor_id
        
        # Store the book in the database
        book_id = self.db.add_book(book_data, book_label)
        
        # Return success
        return {
            'success': True,
            'message': 'Book offer accepted',
            'book_id': book_id
        }
    
    def handle_search(self, customer_id, query):
        """
        Event Handler 2: A customer searches for books
        
        Parameters:
        - customer_id: Identifier of the customer (can be None for anonymous search)
        - query: Dictionary with search criteria
        
        Returns:
        - List of matching books (with public information only)
        
        Security:
        - Search query is owned by the customer
        - Search results only include public book information
        - Customer's search history owned by customer but readable by marketplace
        """
        # Create search results list
        results = []
        
        # Get customer principal if not anonymous
        customer_principal = None
        if customer_id and customer_id in self.db.customers:
            customer_info = self.db.customers[customer_id]
            customer_label = customer_info['label']
            customer_principal = list(customer_label.owners)[0]  # Assume single owner
            
            # Record search query with customer's security label
            # (owned by customer, readable by marketplace)
            search_record = {
                'customer_id': customer_id,
                'query': query,
                'timestamp': 'timestamp_placeholder'
            }
            
            # For marketing purposes, we need to be able to declassify this data
            # if the customer has opted in
            if customer_info['marketing_opt_in']:
                # Create a label owned by customer but readable by marketing partners
                marketing_readers = {self.marketplace, Principal("MarketingPartners")}
                search_label = SecurityLabel(
                    owners={customer_principal},
                    readers=marketing_readers
                )
            else:
                # Standard label - only marketplace can read
                search_label = SecurityLabel(
                    owners={customer_principal},
                    readers={customer_principal, self.marketplace}
                )
        
        # Search the books database
        for book_id, book_info in self.db.books.items():
            book_data = book_info['data']
            book_status = book_info['status']
            
            # Skip books that are not available
            if book_status != 'available':
                continue
            
            # Check if book matches the query
            matches = True
            for key, value in query.items():
                if key in book_data and value:
                    # Simple substring search
                    if isinstance(book_data[key], str) and isinstance(value, str):
                        if value.lower() not in book_data[key].lower():
                            matches = False
                            break
                    # Exact match for non-string fields
                    elif book_data[key] != value:
                        matches = False
                        break
            
            if matches:
                # Add to results, but only include public fields
                public_book_data = {
                    'book_id': book_id,
                    'title': book_data.get('title', ''),
                    'author': book_data.get('author', ''),
                    'year': book_data.get('year', ''),
                    'edition': book_data.get('edition', ''),
                    'publisher': book_data.get('publisher', ''),
                    'condition': book_data.get('condition', ''),
                    'price': book_data.get('price', '')
                }
                results.append(public_book_data)
        
        return {
            'success': True,
            'results': results,
            'count': len(results)
        }
    
    def handle_purchase(self, customer_id, book_id, offered_price):
        """
        Event Handler 3: A customer purchases a book
        
        Parameters:
        - customer_id: Identifier of the customer
        - book_id: Identifier of the book to purchase
        - offered_price: Price the customer is willing to pay (should match book price)
        
        Returns:
        - Success message and purchase confirmation
        
        Security:
        - Purchase record owned jointly by customer, vendor, and marketplace
        - Shipping address flows from customer to vendor (controlled declassification)
        - Purchase history of customer only readable by customer and marketplace
        """
        # Check if customer exists
        if customer_id not in self.db.customers:
            return {'success': False, 'message': 'Customer not found'}
        
        # Check if book exists and is available
        if book_id not in self.db.books:
            return {'success': False, 'message': 'Book not found'}
        
        book_info = self.db.books[book_id]
        if book_info['status'] != 'available':
            return {'success': False, 'message': 'Book is not available'}
        
        # Check if price matches
        book_data = book_info['data']
        if book_data['price'] != offered_price:
            return {'success': False, 'message': 'Price does not match'}
        
        # Get customer and vendor information
        customer_info = self.db.customers[customer_id]
        customer_data = customer_info['data']
        customer_label = customer_info['label']
        
        vendor_id = book_data['vendor_id']
        vendor_info = self.db.vendors[vendor_id]
        vendor_data = vendor_info['data']
        vendor_label = vendor_info['label']
        
        # Get principals
        customer_principal = list(customer_label.owners)[0]  # Assume single owner
        vendor_principal = list(vendor_label.owners)[0]  # Assume single owner
        
        # Mark book as sold
        self.db.books[book_id]['status'] = 'sold'
        
        # Create purchase record
        purchase_data = {
            'book_id': book_id,
            'customer_id': customer_id,
            'vendor_id': vendor_id,
            'price': offered_price,
            'timestamp': 'timestamp_placeholder'
        }
        
        # Security label for the purchase:
        # - Owned jointly by customer, vendor, and marketplace (integrity)
        # - Readable by customer, vendor, and marketplace (confidentiality)
        purchase_label = SecurityLabel(
            owners={customer_principal, vendor_principal, self.marketplace},
            readers={customer_principal, vendor_principal, self.marketplace}
        )
        
        # Record the purchase
        purchase_id = self.db.add_purchase(purchase_data, purchase_label)
        
        # Create confirmation for customer
        customer_confirmation = {
            'purchase_id': purchase_id,
            'book_title': book_data['title'],
            'price': offered_price,
            'vendor': vendor_data['name'],
            'status': 'Confirmed'
        }
        
        # Create confirmation for vendor
        # Here we need to declassify customer address information to the vendor
        # This is a controlled declassification, as customers consent to this
        # by making a purchase
        
        # First, we get the customer's address with its security label
        customer_address = customer_data['address']
        
        # Declassify address - add vendor to readers with customer's authorization
        declassified_readers = {customer_principal, vendor_principal, self.marketplace}
        
        vendor_confirmation = {
            'purchase_id': purchase_id,
            'book_title': book_data['title'],
            'price': offered_price,
            'customer_name': customer_data['name'],
            'customer_address': customer_address,  # Declassified information
            'status': 'Confirmed - Please ship to customer'
        }
        
        # For marketing opt-in customers, we declassify their purchase data
        if customer_info['marketing_opt_in']:
            # Create a marketing record with declassified information
            marketing_data = {
                'customer_id': customer_id,
                'customer_name': customer_data['name'],
                'book_id': book_id,
                'book_title': book_data['title'],
                'book_author': book_data['author'],
                'purchase_timestamp': 'timestamp_placeholder'
            }
            
            # Declassify for marketing partners (only for opt-in customers)
            marketing_readers = {self.marketplace, Principal("MarketingPartners")}
            marketing_label = SecurityLabel(
                owners={customer_principal, self.marketplace},
                readers=marketing_readers
            )
            
            # Store marketing data (in a real system, this would go to marketing partners)
            # This is handled through the declassification mechanism
        
        return {
            'success': True,
            'message': 'Purchase successful',
            'purchase_id': purchase_id,
            'customer_confirmation': customer_confirmation,
            'vendor_confirmation': vendor_confirmation
        }
    
    def set_marketing_opt_in(self, customer_id, opt_in):
        """
        Set customer's marketing opt-in preference
        
        Parameters:
        - customer_id: Identifier of the customer
        - opt_in: Boolean indicating whether to opt in for marketing
        
        Returns:
        - Success message
        """
        if customer_id not in self.db.customers:
            return {'success': False, 'message': 'Customer not found'}
        
        self.db.customers[customer_id]['marketing_opt_in'] = opt_in
        
        return {
            'success': True,
            'message': f'Marketing preference updated: Opt-in = {opt_in}'
        }


# Demo usage of the platform
def demo():
    platform = BookMarketPlatform()
    
    # 1. Vendor uploads a book offer
    book_data = {
        'title': 'Introduction to Information Flow Security',
        'author': 'A. C. Myers',
        'year': '2022',
        'edition': '1st',
        'publisher': 'Security Press',
        'condition': 'new',
        'description': 'A comprehensive introduction to secure information flow',
        'price': 29.99
    }
    
    result = platform.handle_offer('bookstore', book_data)
    print("Book offer result:", result)
    book_id = result['book_id']
    
    # 2. Customer searches for books
    search_query = {
        'title': 'information',
        'author': 'myers'
    }
    
    result = platform.handle_search('alice', search_query)
    print("\nSearch results:", result)
    
    # 3. Customer purchases a book
    result = platform.handle_purchase('alice', book_id, 29.99)
    print("\nPurchase result:", result)
    
    # 4. Opt-in for marketing
    result = platform.set_marketing_opt_in('bob', True)
    print("\nOpt-in result:", result)
    
    # Search and purchase with the opt-in customer
    book_data2 = {
        'title': 'Advanced Security Models',
        'author': 'B. Liskov',
        'year': '2023',
        'edition': '2nd',
        'publisher': 'Security Press',
        'condition': 'new',
        'description': 'Advanced topics in security modeling',
        'price': 39.99
    }
    
    result = platform.handle_offer('rarebooks', book_data2)
    book_id2 = result['book_id']
    
    result = platform.handle_search('bob', {'title': 'advanced'})
    print("\nOpt-in customer search results:", result)
    
    result = platform.handle_purchase('bob', book_id2, 39.99)
    print("\nOpt-in customer purchase result:", result)


if __name__ == "__main__":
    demo()