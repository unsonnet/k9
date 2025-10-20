#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
errors.py
Custom exception hierarchy for the ModelSchema preprocessor.

Provides clear, actionable error messages that hide Python implementation
details and present errors in terms of the ModelSchema language constructs.
"""

from __future__ import annotations
from typing import List, Optional


class PreprocessorError(Exception):
    """Base class for all preprocessor errors."""
    
    def __init__(self, message: str, location: Optional[str] = None):
        self.message = message
        self.location = location
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.location:
            return f"Error in {self.location}: {self.message}"
        return f"Error: {self.message}"


class ParseError(PreprocessorError):
    """Syntax error in ModelSchema or REST API source files."""
    
    def __init__(self, message: str, file_path: str, line: Optional[int] = None):
        self.file_path = file_path
        self.line = line
        location = f"{file_path}" + (f":{line}" if line else "")
        super().__init__(message, location)


class ModelNotFoundError(PreprocessorError):
    """Referenced model does not exist in any accessible namespace."""
    
    def __init__(self, namespace: str, model_name: str, available_models: List[str], 
                 reference_location: Optional[str] = None, all_models: Optional[List[str]] = None):
        self.namespace = namespace
        self.model_name = model_name
        self.available_models = available_models
        
        message = f"Model '{model_name}' not found in namespace '{namespace}'"
        if available_models:
            message += f"\n  Available models in '{namespace}': {', '.join(sorted(available_models))}"
        else:
            message += f"\n  No models found in namespace '{namespace}'"
        
        # Suggest similar model names from the same namespace
        similar = self._find_similar_names(model_name, available_models)
        if similar:
            message += f"\n  Did you mean: {', '.join(similar)}?"
        
        # If no similar models in the namespace, suggest from all models
        elif all_models:
            similar_global = self._find_similar_names(model_name, all_models)
            if similar_global:
                message += f"\n  Similar models found elsewhere: {', '.join(similar_global)}"
                message += f"\n  (Check your import statements or namespace references)"
        
        super().__init__(message, reference_location)
    
    def _find_similar_names(self, target: str, candidates: List[str]) -> List[str]:
        """Find similar model names using simple string distance."""
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            return previous_row[-1]
        
        # Find names with distance <= 2 and length similarity
        similar = []
        for candidate in candidates:
            if abs(len(candidate) - len(target)) <= 2:
                distance = levenshtein_distance(target.lower(), candidate.lower())
                if distance <= 2:
                    similar.append(candidate)
        
        return similar[:3]  # Limit to 3 suggestions


class NamespaceNotFoundError(PreprocessorError):
    """Referenced namespace does not exist."""
    
    def __init__(self, namespace_path: str, available_namespaces: List[str],
                 reference_location: Optional[str] = None):
        self.namespace_path = namespace_path
        self.available_namespaces = available_namespaces
        
        message = f"Namespace '{namespace_path}' not found"
        if available_namespaces:
            # Show only relevant namespaces (similar prefixes)
            relevant = [ns for ns in available_namespaces 
                       if ns.startswith(namespace_path.split('.')[0])]
            if relevant:
                message += f"\n  Similar namespaces: {', '.join(sorted(relevant)[:5])}"
            else:
                message += f"\n  Available namespaces: {', '.join(sorted(available_namespaces)[:10])}"
                if len(available_namespaces) > 10:
                    message += f" (and {len(available_namespaces) - 10} more)"
        
        super().__init__(message, reference_location)


class ImportError(PreprocessorError):
    """Error in import statement resolution."""
    
    def __init__(self, import_path: str, alias: Optional[str] = None, 
                 file_path: Optional[str] = None):
        self.import_path = import_path
        self.alias = alias
        
        if alias:
            message = f"Cannot import '{import_path}' as '{alias}'"
        else:
            message = f"Cannot import '{import_path}'"
        
        super().__init__(message, file_path)


class CircularReferenceError(PreprocessorError):
    """Circular reference detected between models."""
    
    def __init__(self, reference_chain: List[str]):
        self.reference_chain = reference_chain
        chain_str = " → ".join(reference_chain)
        message = f"Circular reference detected: {chain_str}"
        super().__init__(message)


class FieldReferenceError(PreprocessorError):
    """Error in field type reference (e.g., ``ModelName`` reference)."""
    
    def __init__(self, field_name: str, field_type: str, model_name: str,
                 namespace: str, file_path: Optional[str] = None):
        self.field_name = field_name
        self.field_type = field_type
        self.model_name = model_name
        self.namespace = namespace
        
        message = (f"Field '{field_name}' in model '{model_name}' references "
                  f"unknown type '{field_type}'")
        
        location = f"{namespace}.{model_name}"
        if file_path:
            location = f"{file_path} ({location})"
        
        super().__init__(message, location)


def format_error_summary(errors: List[Exception]) -> str:
    """Format a list of errors into a clear summary."""
    if not errors:
        return "No errors found."
    
    summary = [f"Found {len(errors)} error(s):\n"]
    
    for i, error in enumerate(errors, 1):
        if isinstance(error, PreprocessorError):
            summary.append(f"{i}. {error}")
        else:
            # Fallback for unexpected errors
            summary.append(f"{i}. Unexpected error: {error}")
        summary.append("")  # Empty line between errors
    
    return "\n".join(summary)
