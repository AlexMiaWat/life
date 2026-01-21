"""
Static tests for executor_agent.py - basic functionality validation without external dependencies
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test import
def test_executor_agent_import():
    """Test that executor_agent module can be imported"""
    try:
        from src.agents.executor_agent import create_executor_agent
        assert callable(create_executor_agent)
    except ImportError as e:
        pytest.fail(f"Failed to import executor_agent: {e}")


def test_executor_agent_function_signature():
    """Test that create_executor_agent has correct signature"""
    from src.agents.executor_agent import create_executor_agent
    import inspect

    sig = inspect.signature(create_executor_agent)
    expected_params = [
        'project_dir', 'docs_dir', 'role', 'goal', 'backstory',
        'allow_code_execution', 'verbose', 'use_llm_manager',
        'llm_config_path', 'use_parallel'
    ]

    actual_params = list(sig.parameters.keys())
    assert actual_params == expected_params

    # Check parameter types
    assert sig.parameters['project_dir'].annotation == Path
    assert sig.parameters['docs_dir'].annotation.__name__ == 'Optional'
    assert sig.parameters['role'].annotation == str
    assert sig.parameters['goal'].annotation == str
    assert sig.parameters['backstory'].annotation.__name__ == 'Optional'


def test_llm_wrapper_availability():
    """Test LLM wrapper availability detection"""
    from src.agents import executor_agent

    # Test that LLM_WRAPPER_AVAILABLE is defined
    assert hasattr(executor_agent, 'LLM_WRAPPER_AVAILABLE')
    assert isinstance(executor_agent.LLM_WRAPPER_AVAILABLE, bool)

    # Test that create_llm_for_crewai is properly set
    if executor_agent.LLM_WRAPPER_AVAILABLE:
        assert executor_agent.create_llm_for_crewai is not None
    else:
        assert executor_agent.create_llm_for_crewai is None


@patch('src.agents.executor_agent.Agent')
def test_create_executor_agent_basic_creation(mock_agent_class):
    """Test basic agent creation with mocked dependencies"""
    from src.agents.executor_agent import create_executor_agent

    # Setup mock
    mock_agent = MagicMock()
    mock_agent_class.return_value = mock_agent

    # Test with minimal parameters
    project_dir = Path("/tmp/test_project")
    agent = create_executor_agent(project_dir=project_dir)

    # Verify Agent was created
    mock_agent_class.assert_called_once()
    call_args = mock_agent_class.call_args

    # Check basic parameters
    assert call_args[1]['role'] == "Project Executor Agent"
    assert call_args[1]['goal'] == "Execute todo items for the project, following documentation and best practices"
    assert 'backstory' in call_args[1]
    assert call_args[1]['allow_code_execution'] is True
    assert call_args[1]['verbose'] is True

    # Verify return value
    assert agent == mock_agent


@patch('src.agents.executor_agent.Agent')
@patch('src.agents.executor_agent.Path')
def test_create_executor_agent_with_custom_params(mock_path_class, mock_agent_class):
    """Test agent creation with custom parameters"""
    from src.agents.executor_agent import create_executor_agent

    # Setup mocks
    mock_agent = MagicMock()
    mock_agent_class.return_value = mock_agent
    mock_path = MagicMock()
    mock_path_class.return_value = mock_path

    # Test with custom parameters
    project_dir = Path("/tmp/test_project")
    custom_role = "Custom Agent"
    custom_goal = "Custom goal"
    custom_backstory = "Custom backstory"

    agent = create_executor_agent(
        project_dir=project_dir,
        role=custom_role,
        goal=custom_goal,
        backstory=custom_backstory,
        allow_code_execution=False,
        verbose=False
    )

    # Verify Agent was created with custom parameters
    mock_agent_class.assert_called_once()
    call_args = mock_agent_class.call_args

    assert call_args[1]['role'] == custom_role
    assert call_args[1]['goal'] == custom_goal
    assert call_args[1]['backstory'] == custom_backstory
    assert call_args[1]['allow_code_execution'] is False
    assert call_args[1]['verbose'] is False


@patch('src.agents.executor_agent.Agent')
@patch('src.agents.executor_agent.CodeInterpreterTool')
def test_create_executor_agent_tools(mock_code_tool_class, mock_agent_class):
    """Test that tools are properly configured"""
    from src.agents.executor_agent import create_executor_agent

    # Setup mocks
    mock_agent = MagicMock()
    mock_agent_class.return_value = mock_agent
    mock_tool = MagicMock()
    mock_code_tool_class.return_value = mock_tool

    # Test with code execution enabled
    project_dir = Path("/tmp/test_project")
    agent = create_executor_agent(project_dir=project_dir, allow_code_execution=True)

    # Verify CodeInterpreterTool was created
    mock_code_tool_class.assert_called_once()

    # Verify tools were passed to Agent
    call_args = mock_agent_class.call_args
    assert mock_tool in call_args[1]['tools']


@patch('src.agents.executor_agent.Agent')
def test_create_executor_agent_no_tools_when_disabled(mock_agent_class):
    """Test that no tools are added when code execution is disabled"""
    from src.agents.executor_agent import create_executor_agent

    # Setup mock
    mock_agent = MagicMock()
    mock_agent_class.return_value = mock_agent

    # Test with code execution disabled
    project_dir = Path("/tmp/test_project")
    agent = create_executor_agent(project_dir=project_dir, allow_code_execution=False)

    # Verify tools list is empty
    call_args = mock_agent_class.call_args
    assert call_args[1]['tools'] == []


def test_default_backstory_content():
    """Test that default backstory contains expected content"""
    from src.agents.executor_agent import create_executor_agent

    # Get the default backstory (when backstory=None)
    # We need to call the function and inspect what backstory was used
    with patch('src.agents.executor_agent.Agent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        project_dir = Path("/tmp/test_project")
        create_executor_agent(project_dir=project_dir, backstory=None)

        # Check that Agent was called with a backstory containing expected text
        call_args = mock_agent_class.call_args
        backstory = call_args[1]['backstory']

        assert "automated code agent" in backstory
        assert "software projects" in backstory
        assert "todo list" in backstory
        assert "code quality" in backstory


def test_module_constants():
    """Test that module has expected constants and structure"""
    import src.agents.executor_agent as executor_agent_module

    # Test that the main function is available
    assert hasattr(executor_agent_module, 'create_executor_agent')

    # Test that LLM wrapper variables are defined
    assert hasattr(executor_agent_module, 'LLM_WRAPPER_AVAILABLE')
    assert hasattr(executor_agent_module, 'create_llm_for_crewai')