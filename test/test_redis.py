import pytest
from src.tools.cache import get_cache_key,get_cached_response,set_cached_response


@pytest.mark.redis
def test_redis_cache_key_validation():

    key_1 = get_cache_key("bunu grafik haline getirir misin",thread_id="session_A")
    key_2 = get_cache_key("bunu grafik haline getirir misin",thread_id="session_B")

    assert key_1 != key_2
    assert "session_A" in key_1
    assert "session_B" in key_2

@pytest.mark.redis
def test_redis_cache():
    question ="bunu grafik haline getirir misin"

    data_a = {"data": "ciro_grafigi_A"}
    data_b= {"data": "siparis_grafigi_B"}

    set_cached_response(question,data=data_a,ttl_seconds=60,thread_id="user1")
    set_cached_response(question=question,data=data_b,thread_id="user2",ttl_seconds=60)

    res_user_1 = get_cached_response(question, thread_id="user1")
    res_user_2 = get_cached_response(question, thread_id="user2")

    assert res_user_1 == data_a
    assert res_user_2 == data_b
    assert res_user_1 != res_user_2