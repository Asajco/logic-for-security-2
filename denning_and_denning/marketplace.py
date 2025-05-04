class BookMarketplaceDB:
    def __init__(self):
        # Database of registered customers
        # Security label: PRIVATE (contains addresses)
        self.customers = {
            # customer_id: {"name": name, "address": address, "opt_in_marketing": bool}
        }
        
        # Database of registered vendors
        # Security label: PUBLIC
        self.vendors = {
            # vendor_id: {"name": name}
        }
        
        # Database of book offers
        # Security label: PUBLIC for most fields, VENDOR_ONLY for vendor_id
        self.book_offers = {
            # offer_id: {
            #   "title": title, "author": author, "year": year, 
            #   "edition": edition, "publisher": publisher, 
            #   "condition": condition, "description": description,
            #   "price": price, "vendor_id": vendor_id, "available": True
            # }
        }
        
        # Database of purchases
        # Security label: PRIVATE (contains shipping info)
        self.purchases = {
            # purchase_id: {
            #   "offer_id": offer_id, "customer_id": customer_id,
            #   "timestamp": timestamp, "price": price
            # }
        }


class BookMarketplace:
    def __init__(self):
        self.db = BookMarketplaceDB()
        self.next_offer_id = 1
        self.next_purchase_id = 1
    
    def offer_handler(self, vendor_id, book_info):
        # Security label for vendor_id: VENDOR_ONLY
        # Security label for book_info: PUBLIC
        
        # Check if vendor exists
        if vendor_id not in self.db.vendors:
            return {"success": False, "message": "Vendor not found"}
        
        # Create new offer
        offer_id = self.next_offer_id
        self.next_offer_id += 1
        
        self.db.book_offers[offer_id] = {
            "title": book_info["title"],
            "author": book_info["author"],
            "year": book_info["year"],
            "edition": book_info["edition"],
            "publisher": book_info["publisher"],
            "condition": book_info["condition"],
            "description": book_info["description"],
            "price": book_info["price"],
            "vendor_id": vendor_id,  # VENDOR_ONLY info
            "available": True  # PUBLIC info
        }
        
        # Return success with PUBLIC information only
        return {"success": True, "offer_id": offer_id}
    
    def search_handler(self, query):
        # Security label for query: PUBLIC
        # Security label for result: PUBLIC
        
        results = []
        
        for offer_id, offer in self.db.book_offers.items():
            if not offer["available"]:
                continue
                
            # Simple search: check if any field contains the query string
            for field in ["title", "author", "publisher", "description"]:
                if query.lower() in offer[field].lower():
                    # Only include PUBLIC information in results
                    results.append({
                        "offer_id": offer_id,
                        "title": offer["title"],
                        "author": offer["author"],
                        "year": offer["year"],
                        "condition": offer["condition"],
                        "price": offer["price"]
                    })
                    break
        
        return results
    
    def purchase_handler(self, customer_id, offer_id, price):
        # Security label for customer_id: CUSTOMER_ONLY
        # Security label for offer_id: PUBLIC
        # Security label for price: PUBLIC
        
        # Check if customer exists
        if customer_id not in self.db.customers:
            return {"success": False, "message": "Customer not found"}
        
        # Check if offer exists and is available
        if offer_id not in self.db.book_offers or not self.db.book_offers[offer_id]["available"]:
            return {"success": False, "message": "Book offer not available"}
        
        # Check if price matches
        if self.db.book_offers[offer_id]["price"] != price:
            return {"success": False, "message": "Price does not match"}
        
        # Mark book as sold
        self.db.book_offers[offer_id]["available"] = False
        
        vendor_id = self.db.book_offers[offer_id]["vendor_id"]
        
        # Create purchase record
        purchase_id = self.next_purchase_id
        self.next_purchase_id += 1
        
        self.db.purchases[purchase_id] = {
            "offer_id": offer_id,
            "customer_id": customer_id,
            "timestamp": "2025-05-04 12:00:00",
            "price": price
        }
        
        # Generate confirmations
        # For vendor: can include customer shipping info (PRIVATE -> VENDOR_ONLY flow allowed)
        vendor_confirmation = {
            "purchase_id": purchase_id,
            "book_title": self.db.book_offers[offer_id]["title"],
            "customer_name": self.db.customers[customer_id]["name"],
            "shipping_address": self.db.customers[customer_id]["address"],
            "price": price
        }
        
        # For customer: only PUBLIC info
        customer_confirmation = {
            "purchase_id": purchase_id,
            "book_title": self.db.book_offers[offer_id]["title"],
            "price": price
        }
        
        return {
            "success": True,
            "vendor_confirmation": vendor_confirmation,
            "customer_confirmation": customer_confirmation
        }
    
    def get_marketing_data(self):
        # This function collects data for marketing
        marketing_data = []
        
        for purchase_id, purchase in self.db.purchases.items():
            customer_id = purchase["customer_id"]
            customer = self.db.customers[customer_id]
            
            # Only include data from customers who opted in
            if customer.get("opt_in_marketing", False):
                offer_id = purchase["offer_id"]
                offer = self.db.book_offers[offer_id]
                
                marketing_data.append({
                    "customer_name": customer["name"],
                    "customer_location": customer["address"].split(",")[-1].strip(),  # Just the city
                    "book_title": offer["title"],
                    "book_author": offer["author"],
                    "book_category": self._infer_category(offer)  # Some function to categorize books
                })
        
        return marketing_data
    
    def _infer_category(self, offer):
        # Simple function to infer book category
        # In a real implementation, this would be more sophisticated
        title = offer["title"].lower()
        if "programming" in title or "code" in title or "python" in title:
            return "Computer Science"
        elif "history" in title:
            return "History"
        elif "novel" in title or "fiction" in title:
            return "Fiction"
        else:
            return "General"