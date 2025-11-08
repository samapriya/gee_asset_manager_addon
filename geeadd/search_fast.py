import json
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from urllib.parse import urlparse

import requests
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedGEESearch:
    def __init__(self):
        self.community_datasets = []
        self.main_datasets = []
        self.docs_cache = {}

    @lru_cache(maxsize=100)
    def fetch_docs_content(self, url):
        """Fetch and cache documentation content from URLs"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                text = re.sub('<[^<]+?>', '', response.text)
                return text.lower()
        except Exception as e:
            logger.debug(f"Failed to fetch docs from {url}: {e}")
        return ""

    def load_datasets(self, source='both'):
        """
        Load datasets from specified source(s)

        Args:
            source: 'main', 'community', or 'both' (default)
        """
        if source in ['community', 'both']:
            try:
                r = requests.get(
                    "https://raw.githubusercontent.com/samapriya/awesome-gee-community-datasets/master/community_datasets.json"
                )
                self.community_datasets = r.json()
                logger.info(f"Loaded {len(self.community_datasets)} community datasets")
            except Exception as e:
                logger.error(f"Error loading community datasets: {e}")

        if source in ['main', 'both']:
            try:
                r = requests.get(
                    "https://raw.githubusercontent.com/samapriya/ee-catalog-jsons/refs/heads/main/gee_catalog_formatted.json"
                )
                self.main_datasets = r.json()
                logger.info(f"Loaded {len(self.main_datasets)} main catalog datasets")
            except Exception as e:
                logger.error(f"Error loading main catalog datasets: {e}")

    def get_dataset_fingerprint(self, dataset):
        """
        Create a fingerprint to identify related datasets (subsets/variants)
        Returns tuple of (docs_url, sample_code, provider, tags)
        """
        return (
            dataset.get('docs', ''),
            dataset.get('sample_code', ''),
            dataset.get('provider', ''),
            dataset.get('tags', ''),
            dataset.get('thumbnail', ''),
        )

    def extract_base_title(self, title):
        """
        Extract base title without regional/temporal suffixes
        e.g., "Dataset Name: Afghanistan" -> "Dataset Name"
        """
        # Common patterns for subsets
        patterns = [
            r':\s*[A-Z]{2,3}\s*$',  # Country codes: ": AFG"
            r':\s*\d{4}(?:-\d{4})?\s*$',  # Years: ": 2020" or ": 2020-2021"
            r'\s*-\s*[A-Z][a-z]+\s*$',  # Region names: "- Afghanistan"
            r'\s*\([A-Z]{2,3}\)\s*$',  # Country codes in parens: "(AFG)"
        ]

        base_title = title
        for pattern in patterns:
            base_title = re.sub(pattern, '', base_title)

        return base_title.strip()

    def calculate_relevance_score(self, dataset, keywords, include_docs=False):
        """Calculate relevance score using multiple signals with exact phrase matching"""
        score = 0
        keywords_lower = [k.lower() for k in keywords]

        # Join keywords to check for exact phrase match
        phrase = ' '.join(keywords_lower)

        # Search in title (highest weight)
        title = dataset.get('title', '').lower()
        # Bonus for exact phrase match in title
        if phrase in title:
            score += 20
        # Individual keyword matches
        for keyword in keywords_lower:
            if keyword in title:
                score += 5

        # Search in tags (high weight)
        tags = dataset.get('tags', '').lower()
        # Bonus for exact phrase match in tags
        if phrase in tags:
            score += 10
        # Individual keyword matches
        for keyword in keywords_lower:
            if keyword in tags:
                score += 3

        # Search in provider
        provider = dataset.get('provider', '').lower()
        for keyword in keywords_lower:
            if keyword in provider:
                score += 2

        # Search in thematic group
        thematic = dataset.get('thematic_group', '').lower()
        # Bonus for exact phrase match in thematic group
        if phrase in thematic:
            score += 8
        # Individual keyword matches
        for keyword in keywords_lower:
            if keyword in thematic:
                score += 2

        # Fetch and search documentation content if enabled
        if include_docs and score > 0:
            logger.debug(f"Using detailed documentation search for: {dataset.get('title', 'Unknown')}")
            docs_url = dataset.get('docs')
            if docs_url:
                docs_content = self.fetch_docs_content(docs_url)
                # Bonus for exact phrase in docs
                if phrase in docs_content:
                    score += 3
                # Individual keyword matches
                for keyword in keywords_lower:
                    if keyword in docs_content:
                        score += 1

        return score

    def group_related_datasets(self, scored_results):
        """
        Group datasets that are subsets/variants of the same dataset
        Returns dict with fingerprint as key and list of datasets as value
        """
        groups = defaultdict(list)

        for score, dataset, catalog_source in scored_results:
            fingerprint = self.get_dataset_fingerprint(dataset)
            groups[fingerprint].append((score, dataset, catalog_source))

        return groups

    def format_dataset(self, dataset, index, score, catalog_source='unknown', show_variant_info=False):
        """Format a single dataset for output"""
        dtype = dataset.get('type', 'unknown')
        dataset_id = dataset.get('id', '')

        if dtype == 'image_collection':
            ee_snippet = f"ee.ImageCollection('{dataset_id}')"
        elif dtype == 'image':
            ee_snippet = f"ee.Image('{dataset_id}')"
        elif dtype == 'table':
            ee_snippet = f"ee.FeatureCollection('{dataset_id}')"
        else:
            ee_snippet = f"'{dataset_id}'"

        item = {
            "index": index,
            "relevance_score": score,
            "catalog_source": catalog_source,
            "title": dataset.get('title', 'N/A'),
            "asset_path": ee_snippet,
            "type": dtype,
            "sample_code": dataset.get('sample_code', 'N/A'),
            "provider": dataset.get('provider', 'N/A'),
            "tags": dataset.get('tags', 'N/A'),
            "license": dataset.get('license', 'N/A'),
            "docs": dataset.get('docs', 'N/A'),
            #"thumbnail": dataset.get('thumbnail', 'N/A'),
            #"thematic_group": dataset.get('thematic_group', 'N/A'),
        }

        return item

    def search(self, query, max_results=10, include_docs=False, min_score=None,
               allow_subsets=False, group_strategy='best', source='both',
               docs_candidates_multiplier=4):
        """
        Enhanced search with relevance ranking and duplicate detection

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            include_docs: Whether to fetch and search documentation URLs (uses two-stage search)
            min_score: Minimum relevance score to include in results (default: 1 for basic search, 10 for doc search)
            allow_subsets: If False, groups subsets and shows only representative
            group_strategy: 'best' (highest score), 'first', or 'all' (show count)
            source: 'main', 'community', or 'both' (default) - which catalog(s) to search
            docs_candidates_multiplier: When using include_docs, first get this many candidates (multiplier of max_results)
        """
        # Set default min_score based on whether docs are included
        if min_score is None:
            min_score = 5 if include_docs else 1

        keywords = [k.strip() for k in query.split() if k.strip()]
        results = []

        # Determine which datasets to search
        datasets_to_search = []
        if source in ['community', 'both']:
            datasets_to_search.extend([('community', d) for d in self.community_datasets])
        if source in ['main', 'both']:
            datasets_to_search.extend([('main', d) for d in self.main_datasets])

        logger.info(f"Searching {len(datasets_to_search)} datasets for '{query}'...")

        # Two-stage search when docs are enabled for efficiency
        if include_docs:
            logger.info("Using detailed documentation search")
            # Stage 1: Fast search without docs to get top candidates
            logger.info(f"Stage 1: Fast search (without docs) to find top candidates...")
            stage1_results = []
            for catalog_source, dataset in tqdm(datasets_to_search, desc="Initial search", unit="dataset"):
                score = self.calculate_relevance_score(dataset, keywords, include_docs=False)
                if score >= 1:  # Lower threshold for stage 1
                    stage1_results.append((score, dataset, catalog_source))

            # Sort and take top candidates (more than max_results to account for docs boosting lower scores)
            stage1_results.sort(key=lambda x: x[0], reverse=True)
            num_candidates = max_results * docs_candidates_multiplier
            top_candidates = stage1_results[:num_candidates]

            logger.info(f"Stage 2: Searching docs for top {len(top_candidates)} candidates (min_score={min_score})...")

            # Stage 2: Search docs for top candidates only
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_data = {
                    executor.submit(self.calculate_relevance_score, dataset, keywords, include_docs=True): (score, catalog_source, dataset)
                    for score, dataset, catalog_source in top_candidates
                }

                # Use tqdm to show progress of completed futures
                for future in tqdm(as_completed(future_to_data), total=len(future_to_data),
                                  desc="Searching docs", unit="dataset"):
                    stage1_score, catalog_source, dataset = future_to_data[future]
                    final_score = future.result()
                    if final_score >= min_score:
                        results.append((final_score, dataset, catalog_source))
        else:
            # Single-stage search without docs
            for catalog_source, dataset in tqdm(datasets_to_search, desc="Searching datasets", unit="dataset"):
                score = self.calculate_relevance_score(dataset, keywords, include_docs)
                if score >= min_score:
                    results.append((score, dataset, catalog_source))

        # Sort by relevance score
        results.sort(key=lambda x: x[0], reverse=True)

        logger.info(f"Found {len(results)} results above min_score threshold")

        # Handle subset grouping
        if not allow_subsets:
            groups = self.group_related_datasets(results)
            formatted_results = []
            index = 1

            for fingerprint, group in groups.items():
                if len(group) > 1:
                    # This is a group of subsets
                    group.sort(key=lambda x: x[0], reverse=True)  # Sort by score

                    if group_strategy == 'best':
                        # Show the best one with a note about variants
                        score, dataset, catalog_source = group[0]
                        item = self.format_dataset(dataset, index, score, catalog_source)
                        item['has_variants'] = True
                        item['variant_count'] = len(group)
                        item['variant_note'] = f"This dataset has {len(group)} regional/temporal variants. Use --allow-subsets to see all."
                        formatted_results.append(item)
                        index += 1
                    elif group_strategy == 'first':
                        # Show first match
                        score, dataset, catalog_source = group[0]
                        item = self.format_dataset(dataset, index, score, catalog_source)
                        item['has_variants'] = True
                        item['variant_count'] = len(group)
                        formatted_results.append(item)
                        index += 1
                else:
                    # Single dataset, no grouping needed
                    score, dataset, catalog_source = group[0]
                    item = self.format_dataset(dataset, index, score, catalog_source)
                    formatted_results.append(item)
                    index += 1

                if index > max_results:
                    break
        else:
            # Show all subsets
            formatted_results = []
            for i, (score, dataset, catalog_source) in enumerate(results[:max_results], 1):
                item = self.format_dataset(dataset, i, score, catalog_source)
                formatted_results.append(item)

        return formatted_results


# # Usage examples:
# if __name__ == "__main__":
#     search_engine = EnhancedGEESearch()

#     # Example 1: Search both catalogs (default)
#     logger.info("\n=== Search 'global population' in BOTH catalogs ===")
#     search_engine.load_datasets(source='both')
#     results = search_engine.search("global population", max_results=5)
#     print(json.dumps(results, indent=2))

#     # Example 2: Search with docs
#     logger.info("\n=== Search 'global buildings' with docs ===")
#     results = search_engine.search("global buildings", max_results=5, include_docs=True)
#     print(json.dumps(results, indent=2))
