from epi_annotation.fingerprint import fingerprint_prompt


def test_editing_prompt_content_changes_sha_even_with_same_version(tmp_path):
    """A version name alone can't prove two runs used the same prompt: editing
    the file in place must change the fingerprint, or stale results look fresh."""
    prompt = tmp_path / "system.md"
    prompt.write_text("first version of the prompt")
    before = fingerprint_prompt("v1", str(prompt))

    prompt.write_text("edited prompt text")
    after = fingerprint_prompt("v1", str(prompt))

    assert before.version == after.version == "v1"
    assert before.sha256 != after.sha256
