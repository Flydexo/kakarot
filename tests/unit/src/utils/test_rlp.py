import os
import random

import pytest
import pytest_asyncio
from rlp import decode, encode


@pytest_asyncio.fixture
async def rlp(starknet):
    return await starknet.deploy(
        source="./tests/unit/src/utils/test_rlp.cairo",
        cairo_path=["src"],
        disable_hint_validation=False,
    )


@pytest.fixture
def long_list():
    return list(
        bytes.fromhex(
            "80850430e2340082520894dc544d1aa88ff8bbd2f2aec754b1f1e99e1812fd01801ba0110d8fee1de53df0870e6eb599ed3bf68fb3f1e62c82dfe5976c467c97253b15a03450b73d2aef2009f026bcbf097a257ae7a37eb5d3b73dc0760aefad2b98e327"
        )
    )


@pytest.fixture
def short_list():
    return list(
        bytes.fromhex(
            "80850430e2340082520801801ba0110d8fee1de53df0870e6eb599ed3bf68fb3f1e62c82dfe5976c467c97253b15"
        )
    )


# using https://etherscan.io/getRawTx?tx= to get samples
RAW_TX_SAMPLES = [
    bytes.fromhex(
        "f86e8263eb8505b4f9a92b82753094e688b84b23f322a994a53dbf8e15fa82cdb71127880c0e2d2235b8de888026a02c924804fba1a12e820afb1da9a2a9dd3d23894b908d11431eef22dd36e67ea0a072590d04f3e8846aabdddb6efe67a3881a27ab17d9d45fff60ef46a3bddd27f9"
    ),
    bytes.fromhex(
        "f871018302c89e808506a713e0da82520894e35bbafa0266089f95d745d348b468622805d82b876e00f6f06088e880c080a0081ba82131d62d76d2b836878d2b7949f2ce5de8387f685907226f505df95364a014d781beb05623e5e8836622bfb205127ddc9c398dd04c44a8ce1184cea9527b"
    ),
    bytes.fromhex(
        "f90135010a840adc656b8508d6c03c4a8303088e941111111254fb6c44bac0bed2854e76f90643097d80b8c82e95b6c800000000000000000000000095ad61b0a150d79219dcf64e1e6cc01f0b64c4ce000000000000000000000000000000000000000000006c36df1cfb2498bfc4fa000000000000000000000000000000000000000000000000000000000051a4a60000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000100000000000000003b6d0340773dd321873fe70553acc295b1b49a104d968cc80bd34b36c001a03ef4c950835e3402d10615a9ca96b9143921e378e80d8ceebd5b07710cb03657a028e3f573e7484eff9867045923e61e75d29f65b9af2fb82b7a57a163742eda70"
    ),
    bytes.fromhex(
        "f86f830216c58506676ef5ec826b6c941cedc0f3af8f9841b0a1f5c1a4ddc6e1a1629074880101009bbb1fb5aa8026a0044e77af97e063a12b87fbcc083eae2b4b8daeaac46f967b5dcc82cfa1725192a06a9626195a8430f83676b3c1ca8037bbf5d2108161b0aaf07968a2cd442dc8ef"
    ),
]


@pytest.mark.asyncio
class TestRLP:
    class TestRLPListEncode:
        async def test_should_encode_list_longer_55_bytes(self, rlp, long_list):
            rlp_list = await rlp.test__encode_list(long_list).call()
            data_len = len(long_list)
            data_len_len = (data_len.bit_length() + 7) // 8
            prefix = 0xF7 + data_len_len
            expected_list = [
                prefix,
                *list(data_len.to_bytes(data_len_len, "big")),
                *long_list,
            ]
            assert expected_list == rlp_list.result.data

        async def test_should_encode_list_smaller_55_bytes(self, rlp, short_list):
            rlp_list = await rlp.test__encode_list(short_list).call()
            data_len = len(short_list)
            prefix = 0xC0 + data_len
            expected_list = [prefix, *short_list]
            assert expected_list == rlp_list.result.data

    class TestRLPDecode:
        @pytest.mark.parametrize("data", [
            bytes([random.randint(0, 127)]),
            os.urandom(random.randint(2, 54)),
            os.urandom(random.randint(56, 10000)),
            b'This is a string shorter than 55 bytes',
            b'This is a string longer than 55 bytes, so to make it longer I need to write some more text so the string is actually longer than 55 bytes',
        ])
        async def test_should_match_decode_reference_implementation(self, rlp, data):
            decoded = await rlp.test__rlp_decode_at_index(list(encode(data)), 0).call()
            assert decoded.result.data == list(data)

        @pytest.mark.parametrize("raw_tx", RAW_TX_SAMPLES)
        async def test_should_decode_txns(self, rlp, raw_tx):
            contract_decoded = await rlp.test__rlp_decode_at_index(
                list(raw_tx), 0
            ).call()
            assert contract_decoded.result.is_list == True
            decoded = decode(raw_tx)
            for i in range(0, len(decoded)):
                sub_decoded = await rlp.test__rlp_decode_at_index(
                    contract_decoded.result.data, i
                ).call()
                assert list(decoded[i]) == sub_decoded.result.data
