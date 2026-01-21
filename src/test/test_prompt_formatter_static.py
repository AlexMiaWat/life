"""
Static tests for prompt_formatter.py - basic functionality validation
"""

import pytest
from src.prompt_formatter import PromptFormatter


def test_format_system_prompt_no_agent_role():
    """Test format_system_prompt with no agent role"""
    prompt = PromptFormatter.format_system_prompt()

    assert "autonomous coding agent" in prompt
    assert "You MUST execute tasks without asking questions." in prompt
    assert "You MUST perform actions immediately when given a task." in prompt
    assert "You MUST NOT explain your actions unless explicitly asked." in prompt


def test_format_system_prompt_with_agent_role():
    """Test format_system_prompt with custom agent role"""
    role = "Project Executor Agent"
    prompt = PromptFormatter.format_system_prompt(agent_role=role)

    assert f"an {role}" in prompt
    assert "You MUST execute tasks without asking questions." in prompt


def test_format_task_instruction_basic():
    """Test format_task_instruction with basic parameters"""
    task = "Create a function to calculate fibonacci numbers"
    instruction = PromptFormatter.format_task_instruction(task)

    assert task in instruction
    assert "TASK:" in instruction
    assert "EXECUTE:" in instruction
    assert "REPORT:" in instruction


def test_format_task_instruction_with_context():
    """Test format_task_instruction with context"""
    task = "Fix the bug in the login function"
    context = "The function is in auth.py and the issue is with password validation"
    instruction = PromptFormatter.format_task_instruction(task, context=context)

    assert task in instruction
    assert context in instruction
    assert "CONTEXT:" in instruction


def test_format_task_instruction_with_files():
    """Test format_task_instruction with file list"""
    task = "Update the API endpoints"
    files = ["api.py", "routes.py", "models.py"]
    instruction = PromptFormatter.format_task_instruction(task, files=files)

    assert task in instruction
    assert "FILES:" in instruction
    for file in files:
        assert file in instruction


def test_format_task_instruction_with_requirements():
    """Test format_task_instruction with requirements"""
    task = "Implement user authentication"
    requirements = [
        "Use JWT tokens",
        "Support password hashing",
        "Include login/logout endpoints"
    ]
    instruction = PromptFormatter.format_task_instruction(task, requirements=requirements)

    assert task in instruction
    assert "REQUIREMENTS:" in instruction
    for req in requirements:
        assert req in instruction


def test_format_task_instruction_with_constraints():
    """Test format_task_instruction with constraints"""
    task = "Optimize database queries"
    constraints = [
        "Keep response time under 100ms",
        "Don't change the API interface"
    ]
    instruction = PromptFormatter.format_task_instruction(task, constraints=constraints)

    assert task in instruction
    assert "CONSTRAINTS:" in instruction
    for constraint in constraints:
        assert constraint in instruction


def test_format_task_instruction_with_examples():
    """Test format_task_instruction with examples"""
    task = "Format user input data"
    examples = [
        "Input: 'john doe' -> Output: 'John Doe'",
        "Input: 'mary jane' -> Output: 'Mary Jane'"
    ]
    instruction = PromptFormatter.format_task_instruction(task, examples=examples)

    assert task in instruction
    assert "EXAMPLES:" in instruction
    for example in examples:
        assert example in instruction


def test_format_task_instruction_complex():
    """Test format_task_instruction with all parameters"""
    task = "Implement a REST API for user management"
    context = "This is part of a larger web application"
    files = ["user_api.py", "user_model.py", "test_user_api.py"]
    requirements = ["Use FastAPI", "Include CRUD operations", "Add input validation"]
    constraints = ["Follow REST conventions", "Use async/await"]
    examples = ["GET /users - list all users", "POST /users - create user"]

    instruction = PromptFormatter.format_task_instruction(
        task=task,
        context=context,
        files=files,
        requirements=requirements,
        constraints=constraints,
        examples=examples
    )

    # Check all components are included
    assert task in instruction
    assert context in instruction
    assert "FILES:" in instruction
    assert "REQUIREMENTS:" in instruction
    assert "CONSTRAINTS:" in instruction
    assert "EXAMPLES:" in instruction

    # Check all list items are included
    for file in files:
        assert file in instruction
    for req in requirements:
        assert req in instruction
    for constraint in constraints:
        assert constraint in instruction
    for example in examples:
        assert example in instruction


def test_format_task_instruction_empty_lists():
    """Test format_task_instruction with empty lists"""
    task = "Simple task"
    instruction = PromptFormatter.format_task_instruction(
        task=task,
        files=[],
        requirements=[],
        constraints=[],
        examples=[]
    )

    assert task in instruction
    # Should not include empty sections
    assert "FILES:" not in instruction
    assert "REQUIREMENTS:" not in instruction
    assert "CONSTRAINTS:" not in instruction
    assert "EXAMPLES:" not in instruction


def test_format_task_instruction_none_values():
    """Test format_task_instruction with None values"""
    task = "Task with None values"
    instruction = PromptFormatter.format_task_instruction(
        task=task,
        context=None,
        files=None,
        requirements=None,
        constraints=None,
        examples=None
    )

    assert task in instruction
    # Should not include None sections
    assert "CONTEXT:" not in instruction
    assert "FILES:" not in instruction
    assert "REQUIREMENTS:" not in instruction
    assert "CONSTRAINTS:" not in instruction
    assert "EXAMPLES:" not in instruction


def test_format_task_instruction_formatting():
    """Test that instruction formatting follows expected structure"""
    task = "Test task"
    instruction = PromptFormatter.format_task_instruction(task)

    lines = instruction.strip().split('\n')

    # Should start with TASK:
    assert lines[0].startswith("TASK:")

    # Should have EXECUTE: section
    execute_found = any("EXECUTE:" in line for line in lines)
    assert execute_found

    # Should have REPORT: section
    report_found = any("REPORT:" in line for line in lines)
    assert report_found

    # Should end with completion message
    assert "Report completion when finished." in instruction


def test_format_system_prompt_formatting():
    """Test format_system_prompt formatting"""
    prompt = PromptFormatter.format_system_prompt()

    # Should contain SYSTEM: section
    assert "SYSTEM:" in prompt

    # Should contain CONSTRAINTS: section
    assert "CONSTRAINTS:" in prompt

    # Should end with ready message
    assert prompt.strip().endswith("You are ready to receive tasks.")


def test_class_method_behavior():
    """Test that methods are properly decorated as classmethods"""
    import inspect

    assert isinstance(inspect.getattr_static(PromptFormatter, 'format_system_prompt'), classmethod)
    assert isinstance(inspect.getattr_static(PromptFormatter, 'format_task_instruction'), classmethod)


def test_format_task_instruction_special_characters():
    """Test format_task_instruction handles special characters"""
    task = "Task with special chars: @#$%^&*()_+{}|:<>?[]\\;',./"
    instruction = PromptFormatter.format_task_instruction(task)

    assert task in instruction
    # Should preserve special characters
    assert "@#$%^&*()_+{}|:<>?[]\\;',./" in instruction


def test_format_task_instruction_multiline_content():
    """Test format_task_instruction with multiline content"""
    task = """Multi-line task
with multiple lines
and different content"""

    context = """Multi-line context
with additional information
spanning several lines"""

    instruction = PromptFormatter.format_task_instruction(task, context=context)

    assert "Multi-line task" in instruction
    assert "with multiple lines" in instruction
    assert "Multi-line context" in instruction
    assert "with additional information" in instruction


def test_format_task_instruction_large_content():
    """Test format_task_instruction with large content"""
    task = "Large task"
    large_list = [f"Item number {i}" for i in range(100)]

    instruction = PromptFormatter.format_task_instruction(
        task=task,
        requirements=large_list
    )

    assert task in instruction
    assert "REQUIREMENTS:" in instruction

    # Check that all items are included
    for i in range(100):
        assert f"Item number {i}" in instruction


def test_format_system_prompt_custom_role_special_chars():
    """Test format_system_prompt with custom role containing special characters"""
    role = "Special Agent @#$%^&*()"
    prompt = PromptFormatter.format_system_prompt(agent_role=role)

    assert f"an {role}" in prompt
    assert "You MUST execute tasks" in prompt


def test_format_task_instruction_whitespace_handling():
    """Test format_task_instruction handles whitespace properly"""
    task = "  Task with leading/trailing spaces  "
    instruction = PromptFormatter.format_task_instruction(task)

    # Should preserve the task as-is (not strip it)
    assert task in instruction


def test_methods_return_strings():
    """Test that all methods return strings"""
    prompt = PromptFormatter.format_system_prompt()
    assert isinstance(prompt, str)

    instruction = PromptFormatter.format_task_instruction("test task")
    assert isinstance(instruction, str)

    instruction_with_params = PromptFormatter.format_task_instruction(
        "test", context="ctx", files=["f1"], requirements=["r1"]
    )
    assert isinstance(instruction_with_params, str)


def test_format_task_instruction_empty_task():
    """Test format_task_instruction with empty task"""
    instruction = PromptFormatter.format_task_instruction("")

    assert "TASK:" in instruction
    assert "EXECUTE:" in instruction


def test_format_task_instruction_very_long_content():
    """Test format_task_instruction with very long content"""
    long_task = "Task: " + "A" * 10000  # 10KB task
    instruction = PromptFormatter.format_task_instruction(long_task)

    assert long_task in instruction
    assert len(instruction) > 10000  # Should contain the long task


def test_format_system_prompt_multiple_calls():
    """Test format_system_prompt consistency across multiple calls"""
    prompt1 = PromptFormatter.format_system_prompt()
    prompt2 = PromptFormatter.format_system_prompt()
    prompt3 = PromptFormatter.format_system_prompt("Test Agent")

    assert prompt1 == prompt2
    assert prompt1 != prompt3

    # Different roles should produce different prompts
    assert "Test Agent" in prompt3