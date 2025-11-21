"""
Interactive Demo Script for PRD Review Vector Recall System
Demonstrates all 4 recall scenarios with sample queries
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from neo4j_client import Neo4jClient
from embedding_service import EmbeddingService
from vector_indexer import VectorIndexer
from vector_recall import VectorRecallSystem, RecallResultFormatter
from data_generator import PRDDataGenerator
from config import Config

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.table import Table
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Note: Install 'rich' package for better output formatting: pip install rich")


class PRDVectorDemo:
    """Interactive demo for PRD vector recall system"""

    def __init__(self):
        self.console = Console() if HAS_RICH else None
        self.neo4j_client = None
        self.embedding_service = None
        self.indexer = None
        self.recall_system = None
        self.formatter = RecallResultFormatter()

    def print_header(self, text: str):
        """Print formatted header"""
        if HAS_RICH:
            self.console.print(Panel(text, style="bold blue"))
        else:
            print(f"\n{'=' * 80}\n{text}\n{'=' * 80}")

    def print_info(self, text: str):
        """Print info message"""
        if HAS_RICH:
            self.console.print(f"[cyan]ℹ[/cyan] {text}")
        else:
            print(f"ℹ {text}")

    def print_success(self, text: str):
        """Print success message"""
        if HAS_RICH:
            self.console.print(f"[green]✓[/green] {text}")
        else:
            print(f"✓ {text}")

    def print_error(self, text: str):
        """Print error message"""
        if HAS_RICH:
            self.console.print(f"[red]✗[/red] {text}")
        else:
            print(f"✗ {text}")

    def print_warning(self, text: str):
        """Print warning message"""
        if HAS_RICH:
            self.console.print(f"[yellow]⚠[/yellow] {text}")
        else:
            print(f"⚠ {text}")

    def setup(self):
        """Initialize all components"""
        self.print_header("PRD Review Vector Recall System - Setup")

        try:
            # Validate configuration
            self.print_info("Validating configuration...")
            Config.validate()
            self.print_success("Configuration validated")

            # Initialize Neo4j client
            self.print_info("Connecting to Neo4j...")
            self.neo4j_client = Neo4jClient()
            if self.neo4j_client.verify_connection():
                self.print_success("Neo4j connection established")

            # Get database info
            db_info = self.neo4j_client.get_database_info()
            self.print_info(f"Database: {db_info.get('name')} {db_info.get('version')} ({db_info.get('edition')})")

            # Check vector support
            vector_support = self.neo4j_client.check_vector_support()
            if vector_support:
                self.print_success("Vector index support confirmed")
            else:
                self.print_warning("Vector index support could not be confirmed")
                self.print_warning("This may indicate Community Edition limitations")

            # Initialize embedding service
            self.print_info("Initializing embedding service...")
            self.embedding_service = EmbeddingService()
            if self.embedding_service.test_connection():
                self.print_success("Embedding service ready")

            # Initialize indexer and recall system
            self.indexer = VectorIndexer(self.neo4j_client, self.embedding_service)
            self.recall_system = VectorRecallSystem(self.neo4j_client, self.embedding_service)

            self.print_success("Setup completed successfully!")
            return True

        except Exception as e:
            self.print_error(f"Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_and_import_data(self, num_prds: int = 15):
        """Generate and import PRD data"""
        self.print_header(f"Generating and Importing {num_prds} PRD Scenarios")

        try:
            # Generate data
            self.print_info("Generating PRD scenario data...")
            generator = PRDDataGenerator()
            data = generator.generate_prd_data(num_prds=num_prds)

            self.print_success(f"Generated {data['metadata']['num_prds']} PRDs")
            self.print_success(f"Generated {data['metadata']['num_comments']} review comments")
            self.print_success(f"Generated {data['metadata']['num_risks']} risk assessments")
            self.print_success(f"Generated {data['metadata']['num_recommendations']} recommendations")

            # Save to file
            data_file = generator.save_to_file(data)
            self.print_success(f"Data saved to {data_file}")

            # Clear existing data
            if HAS_RICH:
                clear = self.console.input("[yellow]Clear existing database? (y/N):[/yellow] ")
            else:
                clear = input("Clear existing database? (y/N): ")

            if clear.lower() == 'y':
                self.print_info("Clearing database...")
                self.neo4j_client.clear_database()
                self.print_success("Database cleared")

            # Create constraints
            self.print_info("Creating database constraints...")
            self.neo4j_client.create_constraints()

            # Create vector indexes
            self.print_info("Creating vector indexes...")
            index_results = self.indexer.create_all_indexes()
            for index_name, success in index_results.items():
                if success:
                    self.print_success(f"Created index: {index_name}")
                else:
                    self.print_warning(f"Index creation may have failed: {index_name}")

            # Import data with embeddings
            self.print_info("Importing data and generating embeddings...")
            self.print_warning("This may take a few minutes depending on the number of PRDs...")

            self.indexer.import_data_with_embeddings(str(data_file))

            # Verify import
            node_count = self.neo4j_client.get_node_count()
            rel_count = self.neo4j_client.get_relationship_count()
            self.print_success(f"Import completed: {node_count} nodes, {rel_count} relationships")

            return True

        except Exception as e:
            self.print_error(f"Data import failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def demo_scenario_1(self):
        """Demo: Similar PRD Retrieval"""
        self.print_header("Scenario 1: Similar PRD Retrieval")

        query = "开发一个基于AI的智能客服系统，支持自然语言对话和知识库问答"
        self.print_info(f"Query: {query}")

        results = self.recall_system.find_similar_prds(query, top_k=5)
        print(self.formatter.format_similar_prds(results))

    def demo_scenario_2(self):
        """Demo: Intelligent Review Suggestions"""
        self.print_header("Scenario 2: Intelligent Review Suggestions")

        query = "实施全公司范围的数据隐私保护和安全合规改造"
        self.print_info(f"Query: {query}")

        results = self.recall_system.get_intelligent_review_suggestions(query, top_k=10)
        print(self.formatter.format_review_suggestions(results))

    def demo_scenario_3(self):
        """Demo: Risk Identification"""
        self.print_header("Scenario 3: Potential Risk Identification")

        query = "进行大规模的云基础设施迁移和微服务架构改造"
        self.print_info(f"Query: {query}")

        results = self.recall_system.identify_potential_risks(query, top_k=5)
        print(self.formatter.format_risks(results))

    def demo_scenario_4(self):
        """Demo: Department Knowledge Base Retrieval"""
        self.print_header("Scenario 4: Department Knowledge Base Retrieval")

        departments = ["Tech", "Finance", "Compliance"]

        for dept in departments:
            query = "系统升级和技术改造项目"
            self.print_info(f"Searching {dept} department for: {query}")

            results = self.recall_system.search_department_knowledge_base(
                query,
                department=dept,
                top_k=3
            )
            print(self.formatter.format_knowledge_base(results, dept))

    def interactive_mode(self):
        """Interactive query mode"""
        self.print_header("Interactive Mode")
        self.print_info("Enter your PRD description to get recommendations")
        self.print_info("Commands: 'quit' to exit, 'scenarios' to run demo scenarios")

        while True:
            try:
                if HAS_RICH:
                    user_input = self.console.input("\n[bold green]Your query:[/bold green] ")
                else:
                    user_input = input("\nYour query: ")

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.print_info("Exiting interactive mode...")
                    break

                if user_input.lower() == 'scenarios':
                    self.run_all_scenarios()
                    continue

                # Run all 4 scenarios for user input
                self.print_header(f"Analysis for: {user_input}")

                # Similar PRDs
                similar = self.recall_system.find_similar_prds(user_input, top_k=3)
                print(self.formatter.format_similar_prds(similar))

                # Review suggestions
                suggestions = self.recall_system.get_intelligent_review_suggestions(user_input, top_k=6)
                print(self.formatter.format_review_suggestions(suggestions))

                # Risks
                risks = self.recall_system.identify_potential_risks(user_input, top_k=3)
                print(self.formatter.format_risks(risks))

            except KeyboardInterrupt:
                self.print_info("\nExiting...")
                break
            except Exception as e:
                self.print_error(f"Error: {e}")

    def run_all_scenarios(self):
        """Run all demo scenarios"""
        self.demo_scenario_1()
        input("\nPress Enter to continue to Scenario 2...")

        self.demo_scenario_2()
        input("\nPress Enter to continue to Scenario 3...")

        self.demo_scenario_3()
        input("\nPress Enter to continue to Scenario 4...")

        self.demo_scenario_4()

    def cleanup(self):
        """Cleanup resources"""
        if self.neo4j_client:
            self.neo4j_client.close()
        self.print_info("Resources cleaned up")

    def run(self):
        """Main demo execution"""
        try:
            # Setup
            if not self.setup():
                return

            # Check if data exists
            node_count = self.neo4j_client.get_node_count()

            if node_count == 0:
                self.print_info("No data found in database")
                if HAS_RICH:
                    should_import = self.console.input("[yellow]Generate and import data? (Y/n):[/yellow] ")
                else:
                    should_import = input("Generate and import data? (Y/n): ")

                if should_import.lower() != 'n':
                    if not self.generate_and_import_data(num_prds=15):
                        return
            else:
                self.print_info(f"Found {node_count} nodes in database")

            # Main menu
            while True:
                self.print_header("Main Menu")
                print("1. Run all demo scenarios")
                print("2. Interactive query mode")
                print("3. Generate new data")
                print("4. Database statistics")
                print("5. Exit")

                if HAS_RICH:
                    choice = self.console.input("\n[bold green]Choose option (1-5):[/bold green] ")
                else:
                    choice = input("\nChoose option (1-5): ")

                if choice == '1':
                    self.run_all_scenarios()
                elif choice == '2':
                    self.interactive_mode()
                elif choice == '3':
                    self.generate_and_import_data()
                elif choice == '4':
                    self.show_statistics()
                elif choice == '5':
                    break
                else:
                    self.print_warning("Invalid option")

        except Exception as e:
            self.print_error(f"Demo failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

    def show_statistics(self):
        """Show database statistics"""
        self.print_header("Database Statistics")

        stats_query = """
        MATCH (p:PRD) WITH count(p) AS prd_count
        MATCH (r:ReviewComment) WITH prd_count, count(r) AS review_count
        MATCH (risk:RiskAssessment) WITH prd_count, review_count, count(risk) AS risk_count
        MATCH (d:Department) WITH prd_count, review_count, risk_count, count(d) AS dept_count
        RETURN prd_count, review_count, risk_count, dept_count
        """

        results = self.neo4j_client.execute_query(stats_query)
        if results:
            stats = results[0]
            self.print_info(f"PRDs: {stats['prd_count']}")
            self.print_info(f"Review Comments: {stats['review_count']}")
            self.print_info(f"Risk Assessments: {stats['risk_count']}")
            self.print_info(f"Departments: {stats['dept_count']}")

        # Vector indexes
        indexes = self.indexer.list_vector_indexes()
        self.print_info(f"Vector Indexes: {len(indexes)}")
        for idx in indexes:
            self.print_info(f"  - {idx['name']}: {idx['state']}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   PRD Review Vector Recall System - Interactive Demo        ║
    ║   Based on OpenRouter API + Neo4j Vector Indexes            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    demo = PRDVectorDemo()
    demo.run()
