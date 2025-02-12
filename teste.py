from multiprocessing import Process
from bot import run_bot_sync


process = Process(target=run_bot_sync, args=("7685420657:AAFHJCgkU7FhcAxpAp7ZO_9V2RSM_4F_rBc", '7685420657'))
process.start()