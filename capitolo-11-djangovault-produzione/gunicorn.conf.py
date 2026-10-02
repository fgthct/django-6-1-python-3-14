import multiprocessing
import os

bind = os.environ.get("BIND", "0.0.0.0:8000")
# Un worker sincrono gestisce una richiesta alla volta: servono più worker che core.
workers = int(os.environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
timeout = 60
graceful_timeout = 30
worker_tmp_dir = "/dev/shm"  # noqa: S108 - i file di controllo dei worker in RAM, non sul disco del container
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(M)sms'
