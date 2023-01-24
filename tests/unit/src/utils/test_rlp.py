import random

import pytest
import pytest_asyncio
from rlp import Serializable, decode, encode
from rlp.sedes import big_endian_int, binary

random.seed(0)


@pytest_asyncio.fixture
async def rlp(starknet):
    return await starknet.deploy(
        source="./tests/unit/src/utils/test_rlp.cairo",
        cairo_path=["src"],
        disable_hint_validation=False,
    )


@pytest.fixture
def long_list():
    return [
        random.randbytes(random.randint(2, 25)) for i in range(0, random.randint(1, 20))
    ]


@pytest.fixture
def short_list():
    return [
        random.randbytes(random.randint(2, 4)) for i in range(0, random.randint(1, 11))
    ]


class LegacyTx(Serializable):
    fields = [
        ("nonce", big_endian_int),
        ("gas_price", big_endian_int),
        ("gas", big_endian_int),
        ("to", binary),
        ("value", big_endian_int),
        ("data", binary),
        ("v", big_endian_int),
        ("r", binary),
        ("s", binary),
    ]


class EIP1559Tx(Serializable):
    fields = [
        ("chain_id", big_endian_int),
        ("nonce", big_endian_int),
        ("max_priority_fee_per_gas", big_endian_int),
        ("max_fee_per_gas", big_endian_int),
        ("gas", big_endian_int),
        ("to", binary),
        ("value", big_endian_int),
        ("data", binary),
        ("access_list", binary),
        ("v", big_endian_int),
        ("r", binary),
        ("s", binary),
    ]


# using https://etherscan.io/getRawTx?tx= to get samples
RAW_TX_SAMPLES = [
    encode(
        LegacyTx(
            25579,
            24511097131,
            30000,
            bytes.fromhex("e688b84b23f322a994A53dbF8E15FA82CDB71127"),
            868681403082530440,
            bytes.fromhex(""),
            38,
            bytes.fromhex(
                "2c924804fba1a12e820afb1da9a2a9dd3d23894b908d11431eef22dd36e67ea0"
            ),
            bytes.fromhex(
                "72590d04f3e8846aabdddb6efe67a3881a27ab17d9d45fff60ef46a3bddd27f9"
            ),
        )
    ),
    encode(
        LegacyTx(
            10403,
            32072364609,
            30000,
            bytes.fromhex("388C818CA8B9251b393131C08a736A67ccB19297"),
            33732264784808523,
            bytes.fromhex(""),
            38,
            bytes.fromhex(
                "aa6b04aa14c19635d830f9d3247b748e457a4d3ac44e69cbc6e32410dff8fb7a"
            ),
            bytes.fromhex(
                "0b12fdaca6c8790e6fc00c806927b6e92b083e848469ac6007a302cb9cb56dd5"
            ),
        )
    ),
    encode(
        EIP1559Tx(
            1,
            14174,
            1000000000,
            56733056046,
            139959,
            bytes.fromhex("E47c80e8c23f6B4A1aE41c34837a0599D5D16bb0"),
            0,
            bytes.fromhex(
                "de0e9a3e00000000000000000000000000000000000000000000d3bdd3766b7cf9240000"
            ),
            bytes.fromhex(""),
            1,
            bytes.fromhex(
                "dcda2b00db94cdb3df3954b183bdeed54b35af380ba6c1b3e13b8cdd98fdd90b"
            ),
            bytes.fromhex(
                "5d753806a064db6e52a258b253077a647cc1757488fa2ccf45bb2a49f5bde850"
            ),
        )
    ),
    encode(
        LegacyTx(
            136901,
            27505128940,
            27500,
            bytes.fromhex("1CeDC0f3Af8f9841B0a1F5c1a4DDc6e1a1629074"),
            72339737873986986,
            bytes.fromhex(""),
            38,
            bytes.fromhex(
                "044e77af97e063a12b87fbcc083eae2b4b8daeaac46f967b5dcc82cfa1725192"
            ),
            bytes.fromhex(
                "6a9626195a8430f83676b3c1ca8037bbf5d2108161b0aaf07968a2cd442dc8ef"
            ),
        )
    ),
]


@pytest.mark.asyncio
class TestRLP:
    class TestRLPListEncode:
        async def test_should_encode_list_longer_55_bytes(self, rlp, long_list):
            encoded = list(encode(long_list))
            rlp_list = await rlp.test__encode_list(
                encoded[1 + encoded[0] - 0xF7 :]
            ).call()
            assert encoded == rlp_list.result.data

        async def test_should_encode_list_smaller_55_bytes(self, rlp, short_list):
            encoded = list(encode(short_list))
            rlp_list = await rlp.test__encode_list(encoded[1:]).call()
            assert encoded == rlp_list.result.data

    class TestRLPDecode:
        @pytest.mark.parametrize(
            "data",
            [
                bytes([random.randint(0, 127)]),
                random.randbytes(random.randint(2, 54)),
                random.randbytes(random.randint(56, 10000)),
            ],
        )
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
