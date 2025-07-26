#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Smart Reminders App
Tests all CRUD operations and basic endpoints
"""

import requests
import json
import sys
from datetime import datetime
import time

# Get backend URL from frontend .env
BACKEND_URL = "https://6ddeaecd-e963-40bd-afdb-12b7c0127bef.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.created_reminder_id = None
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })
        
    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n=== Testing Basic Endpoints ===")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("GET /api/", True, f"Root endpoint working. Response: {data}")
                else:
                    self.log_test("GET /api/", False, f"Unexpected response format: {data}")
            else:
                self.log_test("GET /api/", False, f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/", False, f"Request failed: {str(e)}")
            
        # Test health check endpoint
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("GET /api/health", True, f"Health check working. Response: {data}")
                else:
                    self.log_test("GET /api/health", False, f"Unexpected health response: {data}")
            else:
                self.log_test("GET /api/health", False, f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/health", False, f"Request failed: {str(e)}")
    
    def test_create_reminder(self):
        """Test creating a new reminder"""
        print("\n=== Testing Create Reminder ===")
        
        reminder_data = {
            "text": "Take a break and stretch!",
            "interval_minutes": 5
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/reminders",
                json=reminder_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "text", "interval_minutes", "is_active", "created_at", "updated_at"]
                
                if all(field in data for field in required_fields):
                    self.created_reminder_id = data["id"]
                    self.log_test("POST /api/reminders", True, 
                                f"Reminder created successfully. ID: {data['id']}", data)
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("POST /api/reminders", False, 
                                f"Missing required fields: {missing_fields}")
            else:
                self.log_test("POST /api/reminders", False, 
                            f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/reminders", False, f"Request failed: {str(e)}")
    
    def test_get_all_reminders(self):
        """Test getting all reminders"""
        print("\n=== Testing Get All Reminders ===")
        
        try:
            response = self.session.get(f"{self.base_url}/reminders")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/reminders", True, 
                                f"Retrieved {len(data)} reminders", data)
                else:
                    self.log_test("GET /api/reminders", False, 
                                f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/reminders", False, 
                            f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/reminders", False, f"Request failed: {str(e)}")
    
    def test_get_specific_reminder(self):
        """Test getting a specific reminder by ID"""
        print("\n=== Testing Get Specific Reminder ===")
        
        if not self.created_reminder_id:
            self.log_test("GET /api/reminders/{id}", False, 
                        "No reminder ID available from create test")
            return
            
        try:
            response = self.session.get(f"{self.base_url}/reminders/{self.created_reminder_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.created_reminder_id:
                    self.log_test("GET /api/reminders/{id}", True, 
                                f"Retrieved reminder successfully", data)
                else:
                    self.log_test("GET /api/reminders/{id}", False, 
                                f"ID mismatch. Expected: {self.created_reminder_id}, Got: {data.get('id')}")
            else:
                self.log_test("GET /api/reminders/{id}", False, 
                            f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/reminders/{id}", False, f"Request failed: {str(e)}")
    
    def test_update_reminder(self):
        """Test updating a reminder"""
        print("\n=== Testing Update Reminder ===")
        
        if not self.created_reminder_id:
            self.log_test("PUT /api/reminders/{id}", False, 
                        "No reminder ID available from create test")
            return
            
        update_data = {
            "text": "Updated: Take a longer break!",
            "interval_minutes": 10,
            "is_active": True
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/reminders/{self.created_reminder_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("text") == update_data["text"] and 
                    data.get("interval_minutes") == update_data["interval_minutes"] and
                    data.get("is_active") == update_data["is_active"]):
                    self.log_test("PUT /api/reminders/{id}", True, 
                                f"Reminder updated successfully", data)
                else:
                    self.log_test("PUT /api/reminders/{id}", False, 
                                f"Update data mismatch. Expected: {update_data}, Got partial: {data}")
            else:
                self.log_test("PUT /api/reminders/{id}", False, 
                            f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("PUT /api/reminders/{id}", False, f"Request failed: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n=== Testing Error Handling ===")
        
        # Test getting non-existent reminder
        try:
            fake_id = "non-existent-id-12345"
            response = self.session.get(f"{self.base_url}/reminders/{fake_id}")
            
            if response.status_code == 404:
                self.log_test("Error Handling - Invalid ID", True, 
                            "Correctly returned 404 for non-existent reminder")
            else:
                self.log_test("Error Handling - Invalid ID", False, 
                            f"Expected 404, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Error Handling - Invalid ID", False, f"Request failed: {str(e)}")
        
        # Test creating reminder with missing fields
        try:
            invalid_data = {"text": "Missing interval"}  # Missing interval_minutes
            response = self.session.post(
                f"{self.base_url}/reminders",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 422:  # FastAPI validation error
                self.log_test("Error Handling - Missing Fields", True, 
                            "Correctly returned 422 for missing required fields")
            else:
                self.log_test("Error Handling - Missing Fields", False, 
                            f"Expected 422, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Error Handling - Missing Fields", False, f"Request failed: {str(e)}")
    
    def test_delete_reminder(self):
        """Test deleting a reminder"""
        print("\n=== Testing Delete Reminder ===")
        
        if not self.created_reminder_id:
            self.log_test("DELETE /api/reminders/{id}", False, 
                        "No reminder ID available from create test")
            return
            
        try:
            response = self.session.delete(f"{self.base_url}/reminders/{self.created_reminder_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("DELETE /api/reminders/{id}", True, 
                                f"Reminder deleted successfully: {data['message']}")
                    
                    # Verify deletion by trying to get the reminder
                    verify_response = self.session.get(f"{self.base_url}/reminders/{self.created_reminder_id}")
                    if verify_response.status_code == 404:
                        self.log_test("DELETE Verification", True, 
                                    "Confirmed reminder was deleted (404 on subsequent GET)")
                    else:
                        self.log_test("DELETE Verification", False, 
                                    f"Reminder still exists after deletion: {verify_response.status_code}")
                else:
                    self.log_test("DELETE /api/reminders/{id}", False, 
                                f"Unexpected response format: {data}")
            else:
                self.log_test("DELETE /api/reminders/{id}", False, 
                            f"Status code {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("DELETE /api/reminders/{id}", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Backend API Tests for: {self.base_url}")
        print(f"⏰ Test started at: {datetime.now()}")
        
        # Run tests in logical order
        self.test_basic_endpoints()
        self.test_create_reminder()
        self.test_get_all_reminders()
        self.test_get_specific_reminder()
        self.test_update_reminder()
        self.test_error_handling()
        self.test_delete_reminder()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)