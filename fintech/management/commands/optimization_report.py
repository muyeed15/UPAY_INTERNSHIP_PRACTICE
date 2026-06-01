from pathlib import Path
from timeit import default_timer

import matplotlib.pyplot as plt

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Prefetch
from fintech.models import Account


class Command(BaseCommand):
    help = "Compare N+1 vs optimized queries"

    def handle(self, *args, **kwargs):
        connection.queries_log.clear()

        t0 = default_timer()
        for a in Account.objects.all():
            u = a.user
            n = a.transactions.count()
        naive_t = default_timer() - t0
        naive_n = len(connection.queries)

        connection.queries_log.clear()

        t0 = default_timer()
        for a in Account.objects.select_related("user").prefetch_related(
            Prefetch("transactions", to_attr="txn_list")
        ):
            u = a.user
            n = len(a.txn_list)
        opt_t = default_timer() - t0
        opt_n = len(connection.queries)

        self.stdout.write("Naive: %d queries (%.3fs)" % (naive_n, naive_t))
        self.stdout.write("Optimized: %d queries (%.3fs)" % (opt_n, opt_t))
        if opt_n > 0 and naive_n > opt_n:
            self.stdout.write(
                "Reduction: %d queries, %.1fx faster"
                % (naive_n - opt_n, naive_t / opt_t)
            )

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
        ax1.bar(["Naive (N+1)", "Optimized"], [naive_n, opt_n], color=["red", "green"])
        ax1.set_title("Query Count")
        ax1.set_ylabel("Queries")
        ax2.bar(["Naive (N+1)", "Optimized"], [naive_t, opt_t], color=["red", "green"])
        ax2.set_title("Execution Time")
        ax2.set_ylabel("Time (s)")
        fig.tight_layout()
        out = Path(__file__).parent / "optimization_chart.png"
        fig.savefig(out)
        self.stdout.write("Chart saved to %s" % out)
