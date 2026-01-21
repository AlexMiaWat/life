"""
Smoke tests for executor_agent.py - basic functionality validation with minimal external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile


class TestExecutorAgentSmoke:
    """Smoke tests for executor agent functionality"""

    def test_create_executor_agent_basic_smoke(self):
        """Smoke test: create agent with basic parameters"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            # Test basic creation
            project_dir = Path("/tmp/test_project")
            agent = create_executor_agent(project_dir=project_dir)

            assert agent is not None
            assert agent == mock_agent

    def test_create_executor_agent_with_docs_dir(self):
        """Smoke test: create agent with docs directory"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")
            docs_dir = Path("/tmp/test_docs")

            agent = create_executor_agent(
                project_dir=project_dir,
                docs_dir=docs_dir
            )

            assert agent is not None

    def test_create_executor_agent_with_all_params(self):
        """Smoke test: create agent with all parameters"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")

            agent = create_executor_agent(
                project_dir=project_dir,
                docs_dir=Path("/tmp/docs"),
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
                allow_code_execution=False,
                verbose=False,
                use_llm_manager=False,
                llm_config_path="test_config.yaml",
                use_parallel=True
            )

            assert agent is not None

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_create_executor_agent_with_openrouter(self):
        """Smoke test: create agent with OpenRouter API key"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class, \
             patch('src.agents.executor_agent.LLM') as mock_llm_class, \
             patch('builtins.open', mock_open(read_data="llm:\n  default_model: test-model\n")), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('yaml.safe_load') as mock_yaml_load:

            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            mock_yaml_load.return_value = {'llm': {'default_model': 'test-model'}}

            project_dir = Path("/tmp/test_project")
            agent = create_executor_agent(project_dir=project_dir)

            assert agent is not None
            # Verify LLM was configured
            call_args = mock_agent_class.call_args
            assert 'llm' in call_args[1]

    def test_create_executor_agent_without_openrouter(self):
        """Smoke test: create agent without OpenRouter API key"""
        from src.agents.executor_agent import create_executor_agent

        # Ensure no OpenRouter key
        with patch.dict(os.environ, {}, clear=True), \
             patch('src.agents.executor_agent.Agent') as mock_agent_class:

            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")
            agent = create_executor_agent(project_dir=project_dir)

            assert agent is not None

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_create_executor_agent_llm_config_not_found(self):
        """Smoke test: create agent when LLM config file not found"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class, \
             patch('src.agents.executor_agent.LLM') as mock_llm_class, \
             patch('pathlib.Path.exists', return_value=False):

            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm

            project_dir = Path("/tmp/test_project")
            agent = create_executor_agent(project_dir=project_dir)

            assert agent is not None

    def test_create_executor_agent_code_execution_tools(self):
        """Smoke test: verify code execution tools are properly configured"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class, \
             patch('src.agents.executor_agent.CodeInterpreterTool') as mock_tool_class:

            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent
            mock_tool = MagicMock()
            mock_tool_class.return_value = mock_tool

            project_dir = Path("/tmp/test_project")

            # Test with code execution enabled
            agent = create_executor_agent(project_dir=project_dir, allow_code_execution=True)

            # Verify tool was created and passed to agent
            mock_tool_class.assert_called_once()
            call_args = mock_agent_class.call_args
            assert mock_tool in call_args[1]['tools']

    def test_create_executor_agent_no_tools_when_disabled(self):
        """Smoke test: verify no tools when code execution disabled"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")

            # Test with code execution disabled
            agent = create_executor_agent(project_dir=project_dir, allow_code_execution=False)

            # Verify no tools were created
            call_args = mock_agent_class.call_args
            assert call_args[1]['tools'] == []

    def test_create_executor_agent_custom_backstory(self):
        """Smoke test: create agent with custom backstory"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")
            custom_backstory = "Custom agent backstory for testing"

            agent = create_executor_agent(
                project_dir=project_dir,
                backstory=custom_backstory
            )

            # Verify custom backstory was used
            call_args = mock_agent_class.call_args
            assert call_args[1]['backstory'] == custom_backstory

    def test_create_executor_agent_default_backstory(self):
        """Smoke test: create agent with default backstory"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")

            agent = create_executor_agent(project_dir=project_dir, backstory=None)

            # Verify default backstory was generated
            call_args = mock_agent_class.call_args
            backstory = call_args[1]['backstory']
            assert isinstance(backstory, str)
            assert len(backstory) > 0
            assert "automated code agent" in backstory

    def test_create_executor_agent_verbose_setting(self):
        """Smoke test: verify verbose setting is passed correctly"""
        from src.agents.executor_agent import create_executor_agent

        with patch('src.agents.executor_agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            project_dir = Path("/tmp/test_project")

            # Test verbose=True (default)
            agent = create_executor_agent(project_dir=project_dir, verbose=True)
            call_args = mock_agent_class.call_args
            assert call_args[1]['verbose'] is True

            # Reset mock
            mock_agent_class.reset_mock()

            # Test verbose=False
            agent = create_executor_agent(project_dir=project_dir, verbose=False)
            call_args = mock_agent_class.call_args
            assert call_args[1]['verbose'] is False