@search_app.command("hybrid")
def cli_search_hybrid(
    query: str = typer.Argument(..., help="The search query text."),
    top_n: int = typer.Option(
        5, "--top-n", "-n", help="Final number of ranked results.", min=1
    ),
    initial_k: int = typer.Option(
        20,
        "--initial-k",
        "-k",
        help="Number of candidates from BM25/Semantic before RRF.",
        min=1,
    ),
    bm25_threshold: float = typer.Option(
        0.01, "--bm25-th", help="BM25 candidate retrieval score threshold.", min=0.0
    ),
    sim_threshold: float = typer.Option(
        0.70,
        "--sim-th",
        help="Similarity candidate retrieval score threshold.",
        min=0.0,
        max=1.0,
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help='Comma-separated list of tags to filter by (e.g., "tag1,tag2").',
    ),
    use_reranking: bool = typer.Option(
        False, "--rerank", help="Enable cross-encoder reranking for improved relevance."
    ),
    reranking_model: str = typer.Option(
        "cross-encoder/ms-marco-MiniLM-L-6-v2", 
        "--rerank-model", 
        "-rm",
        help="Cross-encoder model to use for reranking."
    ),
    reranking_strategy: str = typer.Option(
        "replace", 
        "--rerank-strategy", 
        "-rs",
        help="Strategy for combining original and reranked scores: replace, weighted, max, min."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Combine keyword (BM25) and semantic search results using RRF re-ranking.

    *WHEN TO USE:* Use for the best general-purpose relevance, leveraging both
    keyword matching and conceptual understanding. Often provides more robust
    results than either method alone. Use --rerank to further improve relevance
    with cross-encoder reranking.

    *HOW TO USE:* Provide the query text. Optionally adjust the number of final
    results (`top_n`), initial candidates (`initial_k`), candidate thresholds,
    or add tag filters. Enable cross-encoder reranking with `--rerank` flag.

    *RERANKING:* When enabled with `--rerank`, results are further enhanced with
    cross-encoder reranking, which provides more nuanced relevance judgments by
    analyzing the query-document pairs together instead of separately.
    
    *RERANKING STRATEGIES:*
    - `replace`: Use only the cross-encoder score (default, usually best)
    - `weighted`: Combine original and cross-encoder scores with weights
    - `max`: Take the maximum of original and cross-encoder scores
    - `min`: Take the minimum of original and cross-encoder scores
    """
    logger.info(f"CLI: Performing Hybrid search for '{query}'")
    db = get_db_connection()
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    # Validate reranking strategy if reranking is enabled
    valid_strategies = ["replace", "weighted", "max", "min"]
    if use_reranking and reranking_strategy not in valid_strategies:
        console.print(
            f"[bold red]Error:[/bold red] Invalid reranking strategy: {reranking_strategy}. "
            f"Must be one of: {', '.join(valid_strategies)}"
        )
        raise typer.Exit(code=1)
    
    try:
        # Import the hybrid_search function from the new module if we're using reranking
        if use_reranking:
            try:
                # Try to import the updated version with reranking support
                from arangodb.search_api.hybrid_search_updated import hybrid_search as hybrid_search_with_rerank
                logger.info(f"Using hybrid search with reranking support")
                
                # Use the updated hybrid search function with reranking parameters
                results_data = hybrid_search_with_rerank(
                    db=db,
                    query_text=query,
                    tag_list=tag_list,
                    min_score={
                        "bm25": bm25_threshold,
                        "semantic": sim_threshold
                    },
                    top_n=top_n,
                    initial_k=initial_k,
                    use_reranking=use_reranking,
                    reranking_model=reranking_model,
                    reranking_strategy=reranking_strategy
                )
            except ImportError:
                # Fall back to the standard hybrid search if the updated version isn't available
                logger.warning("Hybrid search with reranking not available, falling back to standard hybrid search")
                console.print(
                    "[yellow]Warning:[/yellow] Reranking support not available in this version. "
                    "Using standard hybrid search."
                )
                results_data = hybrid_search(
                    db, query, top_n, initial_k, bm25_threshold, sim_threshold, tag_list
                )
        else:
            # Use the standard hybrid search function
            results_data = hybrid_search(
                db, query, top_n, initial_k, bm25_threshold, sim_threshold, tag_list
            )
        
        if json_output:
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            # Determine which score field to use for display
            score_field = "hybrid_score"
            if use_reranking and "reranking_applied" in results_data and results_data["reranking_applied"]:
                score_field = "final_score"  # Use the final reranked score for display
            
            # Get table title based on search mode
            search_type = "Hybrid (RRF)"
            if use_reranking and "reranking_applied" in results_data and results_data["reranking_applied"]:
                search_type = "Hybrid with Reranking"
                
            _display_results(results_data, search_type, score_field)
            
            # Display additional reranking info if applied
            if use_reranking and "reranking_applied" in results_data and results_data["reranking_applied"]:
                console.print()
                console.print(
                    f"[bold cyan]Reranking Info:[/bold cyan] Model: [green]{reranking_model.split('/')[-1]}[/green], "
                    f"Strategy: [green]{reranking_strategy}[/green], "
                    f"Time: [green]{results_data.get('reranking_time', 0):.2f}s[/green]"
                )
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during Hybrid search:[/bold red] {e}")
        raise typer.Exit(code=1)