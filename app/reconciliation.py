"""
Reconciliation Engine.

OOP notes for defense:
- `MatchRule` is an ABSTRACT BASE CLASS. Every concrete rule (below)
  INHERITS from it and implements `evaluate()` differently -- that's
  POLYMORPHISM: the Reconciler calls the same method name on different
  rule objects and gets different behaviour.
- Rules are tried in priority order (a simple Chain of Responsibility):
  the first rule whose `evaluate()` returns a result wins.
- `Reconciler` is the ENCAPSULATION boundary: nothing outside this class
  needs to know *how* matching works, only that you call `.run()`.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from collections import defaultdict

from .models import db, Transaction, ReconciliationResult


@dataclass
class RuleResult:
    status: str
    amount_difference: float = 0.0
    details: str = ""


class MatchRule(ABC):
    """Abstract base class for a single pairwise matching rule."""

    @abstractmethod
    def evaluate(self, ho_txn: Transaction, branch_txn: Transaction) -> Optional[RuleResult]:
        """Return a RuleResult if this rule applies, otherwise None."""
        raise NotImplementedError


class ExactMatchRule(MatchRule):
    """Reference matches AND amount matches (within tolerance) -> RECONCILED."""

    def __init__(self, tolerance: float = 0.0):
        self.tolerance = tolerance

    def evaluate(self, ho_txn, branch_txn):
        diff = round(abs(ho_txn.amount - branch_txn.amount), 2)
               if (diff <= self.tolerance
                and ho_txn.currency == branch_txn.currency
                and ho_txn.transaction_date == branch_txn.transaction_date):
            return RuleResult(
                status=ReconciliationResult.STATUS_RECONCILED,
                amount_difference=diff,
                details="Amounts match within tolerance.",
            )
        return None


class AmountMismatchRule(MatchRule):
    """Reference matches, amount differs beyond tolerance -> AMOUNT_MISMATCH."""

    def __init__(self, tolerance: float = 0.0):
        self.tolerance = tolerance

    def evaluate(self, ho_txn, branch_txn):
        diff = round(abs(ho_txn.amount - branch_txn.amount), 2)
        if diff > self.tolerance:
            return RuleResult(
                status=ReconciliationResult.STATUS_AMOUNT_MISMATCH,
                amount_difference=diff,
                details=f"Head Office: {ho_txn.amount}, Branch: {branch_txn.amount}",
            )
        return None

class CurrencyMismatchRule(MatchRule):
    """Reference and amount match, currency differs -> CURRENCY_MISMATCH."""

    def evaluate(self, ho_txn, branch_txn):
        if ho_txn.currency != branch_txn.currency:
            return RuleResult(
                status=ReconciliationResult.STATUS_CURRENCY_MISMATCH,
                details=f"Head Office: {ho_txn.currency}, Branch: {branch_txn.currency}",
            )
        return None


class DateMismatchRule(MatchRule):
    """Reference and amount match, transaction date differs -> DATE_MISMATCH."""

    def evaluate(self, ho_txn, branch_txn):
        if ho_txn.transaction_date != branch_txn.transaction_date:
            return RuleResult(
                status=ReconciliationResult.STATUS_DATE_MISMATCH,
                details=f"Head Office: {ho_txn.transaction_date}, Branch: {branch_txn.transaction_date}",
            )
        return None


class Reconciler:
    """Orchestrates the full reconciliation run for all imported transactions."""

    def __init__(self, tolerance: float = 0.0):
        # Priority order matters: first applicable rule wins.
        self.rules = [
            ExactMatchRule(tolerance=tolerance),
            AmountMismatchRule(tolerance=tolerance),
            CurrencyMismatchRule(),
            DateMismatchRule(),
        ]

    def run(self) -> dict:
        # Clear previous run's results so re-running is idempotent.
        ReconciliationResult.query.delete()

        ho_txns = Transaction.query.filter_by(source=Transaction.SOURCE_HEAD_OFFICE).all()
        branch_txns = Transaction.query.filter_by(source=Transaction.SOURCE_BRANCH).all()

        ho_by_ref = self._group_by_reference(ho_txns)
        branch_by_ref = self._group_by_reference(branch_txns)

        all_refs = set(ho_by_ref.keys()) | set(branch_by_ref.keys())
        summary = defaultdict(int)

        for ref in all_refs:
            ho_group = ho_by_ref.get(ref, [])
            branch_group = branch_by_ref.get(ref, [])

                        # Duplicate detection within a single source.
            has_duplicates = False
            if len(ho_group) > 1:
                self._record_duplicates(ref, ho_group)
                summary[ReconciliationResult.STATUS_DUPLICATE] += len(ho_group)
                has_duplicates = True
            if len(branch_group) > 1:
                self._record_duplicates(ref, branch_group)
                summary[ReconciliationResult.STATUS_DUPLICATE] += len(branch_group)
                has_duplicates = True
            if has_duplicates:
                continue  # held for manual review, never auto-reconciled
            if ho_group and branch_group:
                result = self._evaluate_pair(ho_group[0], branch_group[0])
                summary[result.status] += 1
            elif ho_group and not branch_group:
                self._record_missing(ref, ho_group[0], missing_from="BRANCH")
                summary[ReconciliationResult.STATUS_MISSING] += 1
            elif branch_group and not ho_group:
                self._record_missing(ref, branch_group[0], missing_from="HEAD_OFFICE")
                summary[ReconciliationResult.STATUS_MISSING] += 1

        db.session.commit()
        return dict(summary)

    @staticmethod
    def _group_by_reference(txns):
        grouped = defaultdict(list)
        for t in txns:
            grouped[t.reference_number].append(t)
        return grouped

    def _evaluate_pair(self, ho_txn: Transaction, branch_txn: Transaction) -> RuleResult:
        for rule in self.rules:
            result = rule.evaluate(ho_txn, branch_txn)
            if result is not None:
                db.session.add(ReconciliationResult(
                    reference_number=ho_txn.reference_number,
                    status=result.status,
                    head_office_txn_id=ho_txn.id,
                    branch_txn_id=branch_txn.id,
                    amount_difference=result.amount_difference,
                    details=result.details,
                ))
                return result
        # Should not happen given AmountMismatchRule as catch-all, but be safe.
        fallback = RuleResult(status=ReconciliationResult.STATUS_AMOUNT_MISMATCH, details="Unresolved mismatch.")
        db.session.add(ReconciliationResult(
            reference_number=ho_txn.reference_number,
            status=fallback.status,
            head_office_txn_id=ho_txn.id,
            branch_txn_id=branch_txn.id,
            details=fallback.details,
        ))
        return fallback

    def _record_missing(self, ref, txn: Transaction, missing_from: str):
        is_ho = txn.source == Transaction.SOURCE_HEAD_OFFICE
        db.session.add(ReconciliationResult(
            reference_number=ref,
            status=ReconciliationResult.STATUS_MISSING,
            head_office_txn_id=txn.id if is_ho else None,
            branch_txn_id=txn.id if not is_ho else None,
            missing_from=missing_from,
            details=f"Transaction present in {txn.source} but missing from {missing_from}.",
        ))

    def _record_duplicates(self, ref, txns):
        for t in txns:
            is_ho = t.source == Transaction.SOURCE_HEAD_OFFICE
            db.session.add(ReconciliationResult(
                reference_number=ref,
                status=ReconciliationResult.STATUS_DUPLICATE,
                head_office_txn_id=t.id if is_ho else None,
                branch_txn_id=t.id if not is_ho else None,
                details=f"Duplicate reference number within {t.source} ledger.",
            ))
