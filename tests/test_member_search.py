
import pytest
from src.services.member_service import MemberService

class TestMemberSearch:
    
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)

    def test_search_exact_match(self, member_service):
        member_service.create({"nome": "John Doe", "plano": "Mensal"})
        results = member_service.search_by_name("John Doe")
        assert len(results) == 1
        assert results[0].nome == "John Doe"

    def test_search_partial_match(self, member_service):
        member_service.create({"nome": "Alice Wonderland", "plano": "Mensal"})
        results = member_service.search_by_name("Alice")
        assert len(results) == 1
        assert results[0].nome == "Alice Wonderland"
        
        results_last = member_service.search_by_name("Wonderland")
        assert len(results_last) == 1

    def test_search_case_insensitive(self, member_service):
        member_service.create({"nome": "Bob Builder", "plano": "Mensal"})
        results = member_service.search_by_name("bob")
        assert len(results) == 1
        assert results[0].nome == "Bob Builder"

    def test_search_multiple_tokens(self, member_service):
        # "Pedro Cosme" should match "Pedro Henrique de Menezes Cosme"
        member_service.create({"nome": "Pedro Henrique de Menezes Cosme", "plano": "Mensal"})
        results = member_service.search_by_name("Pedro Cosme")
        assert len(results) == 1
        assert results[0].nome == "Pedro Henrique de Menezes Cosme"

    def test_search_no_results(self, member_service):
        results = member_service.search_by_name("NonExistent")
        assert len(results) == 0
