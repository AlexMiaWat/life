"""
Integration tests for executor_agent.py - testing with real dependencies where possible
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import tempfile
import yaml


class TestExecutorAgentIntegration:
    """Integration tests for executor agent with real dependencies"""

    def test_create_executor_agent_real_dependencies(self):
        """Integration test: create agent with real CrewAI dependencies"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test basic agent creation
            agent = create_executor_agent(project_dir=project_dir)

            # Verify agent was created
            assert agent is not None

            # Verify agent has expected attributes (CrewAI Agent interface)
            assert hasattr(agent, 'role')
            assert hasattr(agent, 'goal')
            assert hasattr(agent, 'backstory')
            assert hasattr(agent, 'tools')

            # Verify role and goal
            assert agent.role == "Project Executor Agent"
            assert "Execute todo items" in agent.goal

    def test_create_executor_agent_with_real_tools(self):
        """Integration test: create agent with real code execution tools"""
        pytest.importorskip("crewai")
        pytest.importorskip("crewai_tools")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test with code execution enabled
            agent = create_executor_agent(
                project_dir=project_dir,
                allow_code_execution=True
            )

            # Verify tools were added
            assert len(agent.tools) > 0

            # Verify tool types (should contain CodeInterpreterTool)
            tool_names = [type(tool).__name__ for tool in agent.tools]
            assert "CodeInterpreterTool" in tool_names

    def test_create_executor_agent_without_tools(self):
        """Integration test: create agent without code execution tools"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test with code execution disabled
            agent = create_executor_agent(
                project_dir=project_dir,
                allow_code_execution=False
            )

            # Verify no tools were added
            assert len(agent.tools) == 0

    def test_create_executor_agent_custom_parameters(self):
        """Integration test: create agent with custom parameters"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            custom_role = "Custom Test Agent"
            custom_goal = "Test goal for integration testing"
            custom_backstory = "Custom backstory for testing"

            agent = create_executor_agent(
                project_dir=project_dir,
                role=custom_role,
                goal=custom_goal,
                backstory=custom_backstory,
                allow_code_execution=False,
                verbose=False
            )

            # Verify custom parameters were set
            assert agent.role == custom_role
            assert agent.goal == custom_goal
            assert agent.backstory == custom_backstory
            assert agent.verbose is False

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_create_executor_agent_openrouter_integration(self):
        """Integration test: create agent with OpenRouter LLM configuration"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create a test LLM config file
            config_path = project_dir / "test_llm_config.yaml"
            config_data = {
                'llm': {
                    'default_model': 'meta-llama/llama-3.2-1b-instruct'
                }
            }

            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            # Test agent creation with LLM config
            agent = create_executor_agent(
                project_dir=project_dir,
                llm_config_path=str(config_path)
            )

            # Verify agent was created successfully
            assert agent is not None
            assert hasattr(agent, 'llm')  # Should have LLM configured

    def test_create_executor_agent_default_backstory_integration(self):
        """Integration test: verify default backstory generation"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test with default backstory
            agent = create_executor_agent(project_dir=project_dir)

            # Verify backstory contains expected content
            backstory = agent.backstory
            assert "automated code agent" in backstory
            assert "software projects" in backstory
            assert "todo list" in backstory
            assert "code quality" in backstory
            assert "best practices" in backstory

    def test_create_executor_agent_with_docs_dir_integration(self):
        """Integration test: create agent with docs directory"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            docs_dir = project_dir / "docs"
            docs_dir.mkdir()

            # Test with docs directory
            agent = create_executor_agent(
                project_dir=project_dir,
                docs_dir=docs_dir
            )

            # Verify agent was created (docs_dir is just passed through, no special handling)
            assert agent is not None
            assert agent.role == "Project Executor Agent"

    def test_create_executor_agent_verbose_modes(self):
        """Integration test: test verbose mode configurations"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Test verbose=True
            agent_verbose = create_executor_agent(
                project_dir=project_dir,
                verbose=True
            )
            assert agent_verbose.verbose is True

            # Test verbose=False
            agent_quiet = create_executor_agent(
                project_dir=project_dir,
                verbose=False
            )
            assert agent_quiet.verbose is False

    def test_create_executor_agent_multiple_instances(self):
        """Integration test: create multiple agent instances"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create multiple agents with different configurations
            agent1 = create_executor_agent(
                project_dir=project_dir,
                role="Agent 1",
                allow_code_execution=True
            )

            agent2 = create_executor_agent(
                project_dir=project_dir,
                role="Agent 2",
                allow_code_execution=False
            )

            # Verify agents are independent instances
            assert agent1 is not agent2
            assert agent1.role != agent2.role
            assert len(agent1.tools) != len(agent2.tools)  # Different tool configurations

    def test_create_executor_agent_project_structure_awareness(self):
        """Integration test: verify agent is aware of project structure"""
        pytest.importorskip("crewai")

        from src.agents.executor_agent import create_executor_agent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            # Create some project structure
            (project_dir / "src").mkdir()
            (project_dir / "tests").mkdir()
            (project_dir / "docs").mkdir()
            (project_dir / "requirements.txt").write_text("pytest\ncrewai\n")

            # Create agent
            agent = create_executor_agent(project_dir=project_dir)

            # Verify agent was created and has access to project path
            assert agent is not None
            # The agent should be able to work with the project structure
            # (This is more of a structural test than functional)