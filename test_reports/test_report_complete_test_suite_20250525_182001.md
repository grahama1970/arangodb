# Test Results Report

**Generated**: 2025-05-25 18:20:01  
**Suite**: complete_test_suite  
**Total Duration**: 90.64s  

---


## Test Suite Summary

| Metric | Value |
|--------|-------|
| **Test Suite** | complete_test_suite |
| **Start Time** | 2025-05-25 18:18:30 |
| **Duration** | 90.64s |
| **Total Tests** | 102 |
| **✅ Passed** | 0 |
| **❌ Failed** | 0 |
| **⚠️ Errors** | 102 |
| **⏭️ Skipped** | 0 |
| **Success Rate** | 0.0% |
| **Status** | ❌ FAILURES DETECTED |



## Detailed Test Results

| Test ID | Module | Status | Duration | Description | ArangoDB Results | Assertion Details |
|---------|--------|--------|----------|-------------|------------------|-------------------|
| `test_all_cli_commands.py::TestAllCLICommands::test_main_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_memory_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_search_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_graph_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_crud_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_episode_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_compaction_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_search_config_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_all_cli_commands.py:85: in test_search_config_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Re... |
| `test_all_cli_commands.py::TestAllCLICommands::test_validate_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_all_cli_commands.py:92: in test_validate_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result ... |
| `test_all_cli_commands.py::TestAllCLICommands::test_community_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_contradiction_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_json_output_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_table_output_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_all_cli_commands.py:147: in test_table_output_consistency
    assert "│" in result.stdout or "┃" in result.stdout or "|" in... |
| `test_all_cli_commands.py::TestAllCLICommands::test_parameter_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_error_handling_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_with_resolution` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_list` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_show` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_multiple_resolutions` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_with_min_size` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_rebuild` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:294: in test_community_rebuild
    data2 = json.loads(result2.stdout)
../../../.local/share/uv/python... |
| `test_community_commands.py::TestCommunityCommands::test_community_list_with_filters` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_list_sorting` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_with_embedding` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_read_by_key` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_read_not_found` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:114: in test_crud_read_not_found
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Res... |
| `test_crud_commands.py::TestCrudCommands::test_crud_update_document` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:130: in test_crud_update_document
    assert data["data"]["price"] == 59.99
E   assert 49.99 == 59.99 |
| `test_crud_commands.py::TestCrudCommands::test_crud_update_with_embedding` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:158: in test_crud_update_with_embedding
    assert data["data"]["content"] == "Completely different conten... |
| `test_crud_commands.py::TestCrudCommands::test_crud_delete_document` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:180: in test_crud_delete_document
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Re... |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_with_filter` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:231: in test_crud_list_with_filter
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <R... |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_empty_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:265: in test_crud_table_output
    assert "_key" in result.stdout
E   assert '_key' in '                  ... |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_invalid_json` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_cross_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_update_nonexistent` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:310: in test_crud_update_nonexistent
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = ... |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_with_special_chars` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:323: in test_crud_create_with_special_chars
    assert result.exit_code == 0
E   assert 1 == 0
E    +  whe... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_create_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:132: in test_episode_create_basic
    data = json.loads(result.stdout)
../../../.local/share/uv/python/... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_create_with_metadata` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:151: in test_episode_create_with_metadata
    data = json.loads(result.stdout)
../../../.local/share/uv... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_all` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:167: in test_episode_list_all
    assert len(episodes) >= 3
E   AssertionError: assert 2 >= 3
E    +  w... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_active_only` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_by_user` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:200: in test_episode_list_by_user
    episodes = json.loads(result.stdout)
../../../.local/share/uv/pyt... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_get_by_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:215: in test_episode_get_by_id
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Re... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_search` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:231: in test_episode_search
    episodes = json.loads(result.stdout)
../../../.local/share/uv/python/cp... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_end` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:248: in test_episode_end
    create_data = json.loads(create_result.stdout)
../../../.local/share/uv/py... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_delete` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:272: in test_episode_delete
    create_data = json.loads(create_result.stdout)
../../../.local/share/uv... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_link_entity` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | ('/home/graham/workspace/experiments/arangodb/tests/arangodb/cli/test_episode_commands.py', 293, 'Skipped: Entities collection not available') |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_invalid_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:349: in test_episode_list_with_limit
    assert data["success"] is True
E   TypeError: list indices mus... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_create_minimal` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:361: in test_episode_create_minimal
    data = json.loads(result.stdout)
../../../.local/share/uv/pytho... |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_relationship` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_duplicate_relationship` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_outbound` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:168: in test_graph_traverse_outbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 =... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_inbound` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:191: in test_graph_traverse_inbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_any_direction` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:214: in test_graph_traverse_any_direction
    assert result.exit_code == 0
E   assert 2 == 0
E    +  wher... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:237: in test_graph_traverse_with_limit
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2... |
| `test_graph_commands.py::TestGraphCommands::test_graph_delete_relationship_by_key` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:264: in test_graph_delete_relationship_by_key
    assert result.exit_code == 0
E   assert 1 == 0
E    +  ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_relationship_with_attributes` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_nonexistent_node` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:293: in test_graph_traverse_nonexistent_node
    assert result.exit_code == 0
E   assert 2 == 0
E    +  w... |
| `test_graph_commands.py::TestGraphCommands::test_graph_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:306: in test_graph_table_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Res... |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_relationship_missing_rationale` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_with_different_depths` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:333: in test_graph_traverse_with_different_depths
    assert result.exit_code == 0
E   assert 2 == 0
E   ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_csv_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:350: in test_graph_traverse_csv_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2... |
| `test_memory_commands.py::TestMemoryCommands::test_memory_create_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_create_with_metadata` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_list_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_list_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_list_by_conversation` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_search_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_search_with_threshold` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_get_by_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_get_invalid_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_history_recent` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_history_by_conversation` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_history_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_create_with_entities` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_search_empty_results` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_bm25_search_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:110: in test_bm25_search_default
    assert len(data["data"]["results"]) > 0
E   assert 0 > 0
E    +  wh... |
| `test_search_commands.py::TestSearchCommands::test_bm25_search_custom_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:133: in test_bm25_search_custom_collection
    assert len(data["data"]["results"]) > 0
E   assert 0 > 0
... |
| `test_search_commands.py::TestSearchCommands::test_semantic_search_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:160: in test_semantic_search_default
    content = res["content"].lower()
E   KeyError: 'content' |
| `test_search_commands.py::TestSearchCommands::test_semantic_search_with_threshold` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_semantic_search_with_tags` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_keyword_search` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:211: in test_keyword_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result... |
| `test_search_commands.py::TestSearchCommands::test_tag_search_single_tag` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:235: in test_tag_search_single_tag
    assert "database" in res["tags"]
E   KeyError: 'tags' |
| `test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_any` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:246: in test_tag_search_multiple_tags_any
    assert result.exit_code == 0
E   assert 2 == 0
E    +  whe... |
| `test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_all` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:264: in test_tag_search_multiple_tags_all
    assert result.exit_code == 0
E   assert 2 == 0
E    +  whe... |
| `test_search_commands.py::TestSearchCommands::test_graph_search` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:308: in test_graph_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result S... |
| `test_search_commands.py::TestSearchCommands::test_search_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_search_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:346: in test_search_table_output
    assert "Content" in result.stdout
E   assert 'Content' in "        ... |
| `test_search_commands.py::TestSearchCommands::test_search_error_handling` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_search_empty_query` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:370: in test_search_empty_query
    assert result.exit_code != 0
E   assert 0 != 0
E    +  where 0 = <Re... |
| `tests/unit/test_community_detection_unit.py::test_init` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_adjacency_matrix` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_modularity` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_small_community_merging` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_empty_graph` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |



## 🗄️ ArangoDB Summary

No database queries executed in this test suite.



## ❌ Failure Details (102 failures)

### test_all_cli_commands.py::TestAllCLICommands::test_main_help - test_main_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_memory_help - test_memory_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_search_help - test_search_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_graph_help - test_graph_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_crud_help - test_crud_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_episode_help - test_episode_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_compaction_help - test_compaction_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_search_config_help - test_search_config_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_all_cli_commands.py:85: in test_search_config_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_all_cli_commands.py::TestAllCLICommands::test_validate_help - test_validate_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_all_cli_commands.py:92: in test_validate_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_all_cli_commands.py::TestAllCLICommands::test_community_help - test_community_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_contradiction_help - test_contradiction_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_json_output_consistency - test_json_output_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_table_output_consistency - test_table_output_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_all_cli_commands.py:147: in test_table_output_consistency
    assert "│" in result.stdout or "┃" in result.stdout or "|" in result.stdout
E   AssertionError: assert ('\u2502' in 'No results found\n' or '\u2503' in 'No results found\n' or '|' in 'No results found\n')
E    +  where 'No results found\n' = <Result okay>.stdout
E    +  and   'No results found\n' = <Result okay>.stdout
E    +  and   'No results found\n' = <Result okay>.stdout
```

---

### test_all_cli_commands.py::TestAllCLICommands::test_parameter_consistency - test_parameter_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_error_handling_consistency - test_error_handling_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_default - test_community_detect_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_with_resolution - test_community_detect_with_resolution

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_list - test_community_list

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_show - test_community_show

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_multiple_resolutions - test_community_detect_multiple_resolutions

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_with_min_size - test_community_detect_with_min_size

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_table_output - test_community_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_rebuild - test_community_rebuild

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:294: in test_community_rebuild
    data2 = json.loads(result2.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_community_commands.py::TestCommunityCommands::test_community_list_with_filters - test_community_list_with_filters

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_list_sorting - test_community_list_sorting

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_basic - test_crud_create_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_with_embedding - test_crud_create_with_embedding

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_read_by_key - test_crud_read_by_key

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_read_not_found - test_crud_read_not_found

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:114: in test_crud_read_not_found
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_update_document - test_crud_update_document

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:130: in test_crud_update_document
    assert data["data"]["price"] == 59.99
E   assert 49.99 == 59.99
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_update_with_embedding - test_crud_update_with_embedding

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:158: in test_crud_update_with_embedding
    assert data["data"]["content"] == "Completely different content about quantum computing"
E   AssertionError: assert 'Original content' == 'Completely different content about quantum computing'
E     
E     - Completely different content about quantum computing
E     + Original content
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_delete_document - test_crud_delete_document

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:180: in test_crud_delete_document
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_default - test_crud_list_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_with_limit - test_crud_list_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_with_filter - test_crud_list_with_filter

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:231: in test_crud_list_with_filter
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_empty_collection - test_crud_list_empty_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_table_output - test_crud_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:265: in test_crud_table_output
    assert "_key" in result.stdout
E   assert '_key' in '                           Documents in test_products                           \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503  Key      \u2503 Name         \u2503 Price \u2503 Category    \u2503 Tags                        \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 prod_001  \u2502 Widget Pro   \u2502 29.99 \u2502 tools       \u2502 ["professional",            \u2502\n\u2502           \u2502              \u2502       \u2502             \u2502 "durable"]...               \u2502\n\u2502 prod_002  \u2502 Gadget Plus  \u2502 49.99 \u2502 electronics \u2502 ["smart", "wireless"]...    \u2502\n\u2502 479291425 \u2502 Test Product \u2502 19.99 \u2502             \u2502                             \u2502\n\u2502 479291547 \u2502 Temp Product \u2502 9.99  \u2502             \u2502                             \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                            Showing 4 of 4 documents                            \n'
E    +  where '                           Documents in test_products                           \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503  Key      \u2503 Name         \u2503 Price \u2503 Category    \u2503 Tags                        \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 prod_001  \u2502 Widget Pro   \u2502 29.99 \u2502 tools       \u2502 ["professional",            \u2502\n\u2502           \u2502              \u2502       \u2502             \u2502 "durable"]...               \u2502\n\u2502 prod_002  \u2502 Gadget Plus  \u2502 49.99 \u2502 electronics \u2502 ["smart", "wireless"]...    \u2502\n\u2502 479291425 \u2502 Test Product \u2502 19.99 \u2502             \u2502                             \u2502\n\u2502 479291547 \u2502 Temp Product \u2502 9.99  \u2502             \u2502                             \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                            Showing 4 of 4 documents                            \n' = <Result okay>.stdout
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_invalid_json - test_crud_create_invalid_json

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_cross_collection - test_crud_cross_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_update_nonexistent - test_crud_update_nonexistent

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:310: in test_crud_update_nonexistent
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_with_special_chars - test_crud_create_with_special_chars

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:323: in test_crud_create_with_special_chars
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_create_basic - test_episode_create_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:132: in test_episode_create_basic
    data = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_create_with_metadata - test_episode_create_with_metadata

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:151: in test_episode_create_with_metadata
    data = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_all - test_episode_list_all

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:167: in test_episode_list_all
    assert len(episodes) >= 3
E   AssertionError: assert 2 >= 3
E    +  where 2 = len([{'_key': 'episode_3277564c1b64', '_id': 'agent_episodes/episode_3277564c1b64', '_rev': '_jukE2Zq---', 'name': 'Feature Development', 'description': 'Working on authentication feature', 'start_time': '2025-05-25T22:18:44.027338+00:00', 'end_time': None, 'entity_count': 0, 'relationship_count': 0, 'metadata': {'user_id': 'dev_user', 'session_id': 'dev_session'}, 'created_at': '2025-05-25T22:18:44.027338+00:00', 'updated_at': '2025-05-25T22:18:44.027338+00:00'}, {'_key': 'episode_b4f6ca422033', '_id': 'agent_episodes/episode_b4f6ca422033', '_rev': '_jukE2Wi---', 'name': 'Test Debugging Session', 'description': 'Debugging test failures', 'start_time': '2025-05-25T22:18:43.977321+00:00', 'end_time': None, 'entity_count': 0, 'relationship_count': 0, 'metadata': {}, 'created_at': '2025-05-25T22:18:43.977321+00:00', 'updated_at': '2025-05-25T22:18:43.977321+00:00'}])
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_active_only - test_episode_list_active_only

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_by_user - test_episode_list_by_user

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:200: in test_episode_list_by_user
    episodes = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_get_by_id - test_episode_get_by_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:215: in test_episode_get_by_id
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_search - test_episode_search

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:231: in test_episode_search
    episodes = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_end - test_episode_end

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:248: in test_episode_end
    create_data = json.loads(create_result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_delete - test_episode_delete

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:272: in test_episode_delete
    create_data = json.loads(create_result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_link_entity - test_episode_link_entity

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
('/home/graham/workspace/experiments/arangodb/tests/arangodb/cli/test_episode_commands.py', 293, 'Skipped: Entities collection not available')
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_table_output - test_episode_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_invalid_id - test_episode_invalid_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_with_limit - test_episode_list_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:349: in test_episode_list_with_limit
    assert data["success"] is True
E   TypeError: list indices must be integers or slices, not str
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_create_minimal - test_episode_create_minimal

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:361: in test_episode_create_minimal
    data = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_relationship - test_graph_add_relationship

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_duplicate_relationship - test_graph_add_duplicate_relationship

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_outbound - test_graph_traverse_outbound

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:168: in test_graph_traverse_outbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_inbound - test_graph_traverse_inbound

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:191: in test_graph_traverse_inbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_any_direction - test_graph_traverse_any_direction

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:214: in test_graph_traverse_any_direction
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_with_limit - test_graph_traverse_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:237: in test_graph_traverse_with_limit
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_delete_relationship_by_key - test_graph_delete_relationship_by_key

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:264: in test_graph_delete_relationship_by_key
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_relationship_with_attributes - test_graph_add_relationship_with_attributes

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_nonexistent_node - test_graph_traverse_nonexistent_node

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:293: in test_graph_traverse_nonexistent_node
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_table_output - test_graph_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:306: in test_graph_table_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_relationship_missing_rationale - test_graph_add_relationship_missing_rationale

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_with_different_depths - test_graph_traverse_with_different_depths

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:333: in test_graph_traverse_with_different_depths
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_csv_output - test_graph_traverse_csv_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:350: in test_graph_traverse_csv_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_memory_commands.py::TestMemoryCommands::test_memory_create_basic - test_memory_create_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_create_with_metadata - test_memory_create_with_metadata

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_list_default - test_memory_list_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_list_with_limit - test_memory_list_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_list_by_conversation - test_memory_list_by_conversation

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_search_basic - test_memory_search_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_search_with_threshold - test_memory_search_with_threshold

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_get_by_id - test_memory_get_by_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_get_invalid_id - test_memory_get_invalid_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_history_recent - test_memory_history_recent

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_history_by_conversation - test_memory_history_by_conversation

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_history_with_limit - test_memory_history_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_table_output - test_memory_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_create_with_entities - test_memory_create_with_entities

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_search_empty_results - test_memory_search_empty_results

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_bm25_search_default - test_bm25_search_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:110: in test_bm25_search_default
    assert len(data["data"]["results"]) > 0
E   assert 0 > 0
E    +  where 0 = len([])
```

---

### test_search_commands.py::TestSearchCommands::test_bm25_search_custom_collection - test_bm25_search_custom_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:133: in test_bm25_search_custom_collection
    assert len(data["data"]["results"]) > 0
E   assert 0 > 0
E    +  where 0 = len([])
```

---

### test_search_commands.py::TestSearchCommands::test_semantic_search_default - test_semantic_search_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:160: in test_semantic_search_default
    content = res["content"].lower()
E   KeyError: 'content'
```

---

### test_search_commands.py::TestSearchCommands::test_semantic_search_with_threshold - test_semantic_search_with_threshold

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_semantic_search_with_tags - test_semantic_search_with_tags

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_keyword_search - test_keyword_search

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:211: in test_keyword_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_tag_search_single_tag - test_tag_search_single_tag

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:235: in test_tag_search_single_tag
    assert "database" in res["tags"]
E   KeyError: 'tags'
```

---

### test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_any - test_tag_search_multiple_tags_any

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:246: in test_tag_search_multiple_tags_any
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_all - test_tag_search_multiple_tags_all

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:264: in test_tag_search_multiple_tags_all
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_graph_search - test_graph_search

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:308: in test_graph_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_search_with_limit - test_search_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_search_table_output - test_search_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:346: in test_search_table_output
    assert "Content" in result.stdout
E   assert 'Content' in "                                Semantic Results                                \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503 Doc                                \u2503 Similarity Score   \u2503 Score              \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 {'_id': 'documents/test_doc_2',    \u2502 0.7861812114715576 \u2502 0.7861812114715576 \u2502\n\u2502 '_key': 'test_doc_...              \u2502                    \u2502                    \u2502\n\u2502 {'_id': 'documents/db_doc_1',      \u2502 0.7752950191497803 \u2502 0.7752950191497803 \u2502\n\u2502 '_key': 'db_doc_1', ...            \u2502                    \u2502                    \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                                Found 2 results                                 \n"
E    +  where "                                Semantic Results                                \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503 Doc                                \u2503 Similarity Score   \u2503 Score              \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 {'_id': 'documents/test_doc_2',    \u2502 0.7861812114715576 \u2502 0.7861812114715576 \u2502\n\u2502 '_key': 'test_doc_...              \u2502                    \u2502                    \u2502\n\u2502 {'_id': 'documents/db_doc_1',      \u2502 0.7752950191497803 \u2502 0.7752950191497803 \u2502\n\u2502 '_key': 'db_doc_1', ...            \u2502                    \u2502                    \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                                Found 2 results                                 \n" = <Result okay>.stdout
```

---

### test_search_commands.py::TestSearchCommands::test_search_error_handling - test_search_error_handling

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_search_empty_query - test_search_empty_query

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:370: in test_search_empty_query
    assert result.exit_code != 0
E   assert 0 != 0
E    +  where 0 = <Result okay>.exit_code
```

---

### tests/unit/test_community_detection_unit.py::test_init - test_init

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_adjacency_matrix - test_adjacency_matrix

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_modularity - test_modularity

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_small_community_merging - test_small_community_merging

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_empty_graph - test_empty_graph

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---



## 📊 Test Execution Timeline

| Test | Start Time | Duration | Status |
|------|------------|----------|--------|
| test_main_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_search_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_compaction_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_search_config_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_validate_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_contradiction_help | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_json_output_consistency | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_table_output_consistency | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_parameter_consistency | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_error_handling_consistency | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_detect_default | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_detect_with_resolution | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_list | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_show | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_detect_multiple_resolutions | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_detect_with_min_size | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_table_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_rebuild | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_list_with_filters | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_community_list_sorting | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_create_basic | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_create_with_embedding | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_read_by_key | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_read_not_found | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_update_document | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_update_with_embedding | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_delete_document | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_list_default | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_list_with_limit | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_list_with_filter | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_list_empty_collection | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_table_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_create_invalid_json | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_cross_collection | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_update_nonexistent | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_crud_create_with_special_chars | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_create_basic | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_create_with_metadata | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_list_all | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_list_active_only | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_list_by_user | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_get_by_id | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_search | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_end | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_delete | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_link_entity | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_table_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_invalid_id | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_list_with_limit | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_episode_create_minimal | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_add_relationship | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_add_duplicate_relationship | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_outbound | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_inbound | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_any_direction | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_with_limit | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_delete_relationship_by_key | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_add_relationship_with_attributes | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_nonexistent_node | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_table_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_add_relationship_missing_rationale | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_with_different_depths | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_csv_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_create_basic | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_create_with_metadata | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_list_default | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_list_with_limit | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_list_by_conversation | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_search_basic | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_search_with_threshold | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_get_by_id | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_get_invalid_id | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_history_recent | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_history_by_conversation | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_history_with_limit | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_table_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_create_with_entities | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_memory_search_empty_results | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_bm25_search_default | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_bm25_search_custom_collection | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_semantic_search_default | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_semantic_search_with_threshold | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_semantic_search_with_tags | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_keyword_search | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_tag_search_single_tag | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_tag_search_multiple_tags_any | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_tag_search_multiple_tags_all | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_graph_search | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_search_with_limit | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_search_table_output | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_search_error_handling | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_search_empty_query | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_init | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_adjacency_matrix | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_modularity | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_small_community_merging | 18:18:30 | 0.000s | ⚠️ ERROR |
| test_empty_graph | 18:18:30 | 0.000s | ⚠️ ERROR |

---

**Report Generation**: Automated via ArangoDB Memory Bank Test Reporter  
**Compliance**: Task List Template Guide v2 Compatible  
**Non-Hallucinated Results**: All data sourced from actual test execution and ArangoDB queries  
