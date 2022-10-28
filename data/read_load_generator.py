from multiprocessing import Pool

import requests

API_SERVICE = "https://3a4dv94r2h.execute-api.eu-central-1.amazonaws.com/prod/items"
N_TIMES = 10000
N_PROC = 16


def call(i):
    resp = requests.get(API_SERVICE)
    print(f"{i+1} call - {resp}", )


if __name__ == '__main__':
    with Pool(N_PROC) as p:
        p.map(call, range(N_TIMES))
