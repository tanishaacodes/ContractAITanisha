"""
Clause Audit Storage Module
Stores clauses as text files for audit trail and compliance
"""

import os
import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ClauseAuditStorage:
    """
    Handles storage of clauses as text files for audit purposes
    """

    def __init__(self, base_dir="data/clause_audit"):
        """
        Initialize audit storage

        Args:
            base_dir: Base directory for clause audit files
        """
        self.base_dir = Path(base_dir)
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """Create audit directory if it doesn't exist"""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Clause audit directory: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create audit directory: {e}")
            raise

    def _get_contract_dir(self, contract_id):
        """Get directory path for a specific contract"""
        # Convert UUID to string for path operations
        contract_id_str = str(contract_id)
        contract_dir = self.base_dir / contract_id_str
        contract_dir.mkdir(parents=True, exist_ok=True)
        return contract_dir

    def save_clauses_to_file(self, contract_id, clauses, metadata=None):
        """
        Save clauses to a text file

        Args:
            contract_id: Contract database ID
            clauses: List of clause dictionaries with text, name, etc.
            metadata: Additional metadata to include

        Returns:
            Path to created file
        """
        try:
            contract_dir = self._get_contract_dir(contract_id)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clauses_{timestamp}.txt"
            filepath = contract_dir / filename

            # Write clauses to file
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 80 + "\n")
                f.write(f"CONTRACT CLAUSE AUDIT TRAIL\n")
                f.write(f"Contract ID: {contract_id}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total Clauses: {len(clauses)}\n")
                f.write("=" * 80 + "\n\n")

                # Write metadata if provided
                if metadata:
                    f.write("METADATA:\n")
                    f.write("-" * 80 + "\n")
                    for key, value in metadata.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")

                # Write each clause
                for idx, clause in enumerate(clauses, 1):
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"CLAUSE #{idx}\n")
                    f.write(f"{'=' * 80}\n\n")

                    # Clause metadata
                    f.write(f"Clause Name: {clause.get('name', 'Unknown')}\n")
                    f.write(f"Clause Type: {clause.get('type', 'N/A')}\n")

                    if 'cluster_label' in clause:
                        f.write(f"Cluster Label: {clause.get('cluster_label')}\n")

                    if 'confidence' in clause:
                        f.write(f"Confidence: {clause.get('confidence'):.2f}\n")

                    f.write(f"\n")

                    # Clause text
                    f.write("TEXT:\n")
                    f.write("-" * 80 + "\n")
                    f.write(clause.get('text', '(No text available)'))
                    f.write("\n")

                    # Separator
                    f.write("\n" + "-" * 80 + "\n")

                # Footer
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF CLAUSE AUDIT TRAIL\n")
                f.write("=" * 80 + "\n")

            logger.info(f"Saved {len(clauses)} clauses to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save clauses to file: {e}")
            raise

    def save_clause_library(self, contract_id, clause_groups, cluster_names):
        """
        Save organized clause library to file

        Args:
            contract_id: Contract database ID
            clause_groups: Dictionary mapping cluster labels to clause lists
            cluster_names: Dictionary mapping cluster labels to generated names

        Returns:
            Path to created file
        """
        try:
            contract_dir = self._get_contract_dir(contract_id)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clause_library_{timestamp}.txt"
            filepath = contract_dir / filename

            # Write organized clauses
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("=" * 80 + "\n")
                f.write(f"CLAUSE LIBRARY - ORGANIZED BY CATEGORY\n")
                f.write(f"Contract ID: {contract_id}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Categories: {len(clause_groups)}\n")
                f.write("=" * 80 + "\n\n")

                # Table of contents
                f.write("TABLE OF CONTENTS:\n")
                f.write("-" * 80 + "\n")
                for label in sorted(clause_groups.keys()):
                    category_name = cluster_names.get(label, f"Category {label}")
                    count = len(clause_groups[label])
                    f.write(f"{label}. {category_name} ({count} clauses)\n")
                f.write("\n")

                # Write each category
                for label in sorted(clause_groups.keys()):
                    category_name = cluster_names.get(label, f"Category {label}")
                    clauses = clause_groups[label]

                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"CATEGORY {label}: {category_name.upper()}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"Total Clauses: {len(clauses)}\n\n")

                    # Write clauses in this category
                    for idx, clause_text in enumerate(clauses, 1):
                        f.write(f"\n{'-' * 80}\n")
                        f.write(f"{category_name} - Clause {idx}\n")
                        f.write(f"{'-' * 80}\n")
                        f.write(clause_text)
                        f.write(f"\n")

                # Footer
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF CLAUSE LIBRARY\n")
                f.write("=" * 80 + "\n")

            logger.info(f"Saved clause library to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save clause library: {e}")
            raise

    def save_json_backup(self, contract_id, data, filename_prefix="clause_data"):
        """
        Save clause data as JSON backup

        Args:
            contract_id: Contract database ID
            data: Data to save as JSON
            filename_prefix: Prefix for filename

        Returns:
            Path to created JSON file
        """
        try:
            contract_dir = self._get_contract_dir(contract_id)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.json"
            filepath = contract_dir / filename

            # Write JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved JSON backup to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save JSON backup: {e}")
            raise

    def get_contract_audit_files(self, contract_id):
        """
        Get list of audit files for a contract

        Args:
            contract_id: Contract database ID

        Returns:
            List of file paths
        """
        try:
            contract_dir = self._get_contract_dir(contract_id)

            if not contract_dir.exists():
                return []

            files = list(contract_dir.glob("*"))
            return [str(f) for f in sorted(files, reverse=True)]

        except Exception as e:
            logger.error(f"Failed to get audit files: {e}")
            return []

    def delete_contract_audit_files(self, contract_id):
        """
        Delete all audit files for a contract

        Args:
            contract_id: Contract database ID

        Returns:
            Success boolean
        """
        try:
            contract_dir = self.base_dir / contract_id

            if not contract_dir.exists():
                return True

            # Delete all files in directory
            for file in contract_dir.glob("*"):
                file.unlink()

            # Remove directory
            contract_dir.rmdir()

            logger.info(f"Deleted audit files for contract: {contract_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete audit files: {e}")
            return False


# Singleton instance
_audit_storage = None


def get_audit_storage():
    """Get or create singleton ClauseAuditStorage instance"""
    global _audit_storage
    if _audit_storage is None:
        _audit_storage = ClauseAuditStorage()
    return _audit_storage
