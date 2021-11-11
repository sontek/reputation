import pytest
import ipaddress
from pathlib import Path

cwd = Path(__file__).parents[0]


@pytest.mark.skip()
@pytest.mark.parametrize(
    ('ipset_filename'),
    (
        # ('firehol_level1.netset'),
        # ('firehol_level2.netset'),
        # ('firehol_level3.netset'),
        # ('firehol_level4.netset'),
        ('firehol_webserver.netset'),
    ),
)
def test_no_overlaps(ipset_filename):
    networks = []

    with open(cwd / 'files' / ipset_filename) as f:
        data = f.readlines()
        for line in data:
            if line.startswith("#"):
                continue

            ip = line.strip()

            if not ip:
                continue

            if '/' not in ip:
                # convert to single IP range
                ip = f"{ip}/32"

            network = ipaddress.IPv4Network(ip)
            networks.append(network)

    for i in range(0, len(networks)):
        for j in range(i+1, len(networks)):
            n1 = networks[i]
            n2 = networks[j]
            assert not n1.overlaps(n2)
