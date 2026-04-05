"""
模型输出签名演示：数字签名 + 文本水印 + 审计日志
对应文章：64-模型输出签名如何证明结果来自你的系统
"""

import hmac
import json
import time
import hashlib
from dataclasses import dataclass, field


@dataclass
class SignedResponse:
    content: str
    response_id: str
    timestamp: float
    model_version: str
    content_hash: str
    signature: str
    watermark_bits: str = ""
    metadata: dict = field(default_factory=dict)


class OutputSigner:
    def __init__(self, secret_key: str, model_version: str = "v1.0"):
        self.secret_key = secret_key.encode()
        self.model_version = model_version
        self.response_counter = 0

    def sign(self, content: str, request_context: dict = None) -> SignedResponse:
        self.response_counter += 1
        response_id = f"resp_{hashlib.md5(f'{time.time()}{self.response_counter}'.encode()).hexdigest()[:16]}"
        timestamp = time.time()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        payload = f"{response_id}|{timestamp}|{content_hash}|{self.model_version}"
        signature = hmac.new(self.secret_key, payload.encode(), hashlib.sha256).hexdigest()
        return SignedResponse(
            content=content, response_id=response_id,
            timestamp=timestamp, model_version=self.model_version,
            content_hash=content_hash, signature=signature,
            metadata=request_context or {},
        )

    def verify(self, response: SignedResponse) -> dict:
        actual_hash = hashlib.sha256(response.content.encode()).hexdigest()
        hash_valid = actual_hash == response.content_hash
        payload = f"{response.response_id}|{response.timestamp}|{response.content_hash}|{response.model_version}"
        expected_sig = hmac.new(self.secret_key, payload.encode(), hashlib.sha256).hexdigest()
        sig_valid = hmac.compare_digest(expected_sig, response.signature)
        return {
            "valid": hash_valid and sig_valid,
            "hash_match": hash_valid,
            "signature_match": sig_valid,
            "response_id": response.response_id,
        }


class TextWatermarker:
    def __init__(self, secret: str):
        self.secret = secret
        self.synonym_pairs = [
            ("因此", "所以"), ("但是", "然而"), ("而且", "并且"),
            ("可以", "能够"), ("需要", "必须"), ("使用", "利用"),
        ]

    def embed(self, text: str, bits: str = "1010") -> str:
        result = text
        bit_idx = 0
        for original, replacement in self.synonym_pairs:
            if bit_idx >= len(bits):
                break
            if original in result:
                if bits[bit_idx] == "1":
                    result = result.replace(original, replacement, 1)
                bit_idx += 1
        return result

    def detect(self, text: str) -> dict:
        detected_bits = []
        for original, replacement in self.synonym_pairs:
            if replacement in text:
                detected_bits.append("1")
            elif original in text:
                detected_bits.append("0")
        return {
            "watermark_detected": len(detected_bits) > 0,
            "bits": "".join(detected_bits),
            "confidence": round(len(detected_bits) / max(len(self.synonym_pairs), 1), 3),
        }


class AuditLogger:
    def __init__(self):
        self.logs: list[dict] = []
        self.hash_chain: str = "genesis"

    def log(self, signed_response: SignedResponse, user_id: str, query: str):
        entry = {
            "sequence": len(self.logs) + 1,
            "response_id": signed_response.response_id,
            "user_id": user_id, "query": query,
            "content_hash": signed_response.content_hash,
            "signature": signed_response.signature,
            "timestamp": signed_response.timestamp,
            "prev_hash": self.hash_chain,
        }
        entry_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        entry["entry_hash"] = entry_hash
        self.hash_chain = entry_hash
        self.logs.append(entry)

    def verify_chain(self) -> dict:
        prev_hash = "genesis"
        for i, entry in enumerate(self.logs):
            if entry["prev_hash"] != prev_hash:
                return {"valid": False, "broken_at": i}
            check = {k: v for k, v in entry.items() if k != "entry_hash"}
            expected = hashlib.sha256(json.dumps(check, sort_keys=True).encode()).hexdigest()
            if expected != entry["entry_hash"]:
                return {"valid": False, "broken_at": i}
            prev_hash = entry["entry_hash"]
        return {"valid": True, "total_entries": len(self.logs)}


def main():
    secret_key = "my-signing-secret-key-2024"
    signer = OutputSigner(secret_key)
    watermarker = TextWatermarker(secret_key)
    audit = AuditLogger()

    print("=" * 60)
    print("模型输出签名演示")
    print("=" * 60)

    # 1. 签名生成与验证
    content = "退货流程：因此您需要先提交申请，但是需要在7天内完成。可以通过APP操作。"
    print(f"\n--- 1. 数字签名 ---")
    print(f"原始内容: {content}")

    signed = signer.sign(content, {"user_id": "u1", "query": "退货流程"})
    print(f"响应ID: {signed.response_id}")
    print(f"内容哈希: {signed.content_hash[:32]}...")
    print(f"签名: {signed.signature[:32]}...")

    verify_result = signer.verify(signed)
    print(f"验证结果: {'✅ 有效' if verify_result['valid'] else '❌ 无效'}")

    # 2. 篡改检测
    print(f"\n--- 2. 篡改检测 ---")
    tampered = SignedResponse(
        content=signed.content + "（已篡改）",
        response_id=signed.response_id,
        timestamp=signed.timestamp,
        model_version=signed.model_version,
        content_hash=signed.content_hash,
        signature=signed.signature,
    )
    tamper_result = signer.verify(tampered)
    print(f"篡改后验证: {'✅ 有效' if tamper_result['valid'] else '❌ 检测到篡改'}")
    print(f"  哈希匹配: {tamper_result['hash_match']}, 签名匹配: {tamper_result['signature_match']}")

    # 3. 文本水印
    print(f"\n--- 3. 文本水印 ---")
    watermarked = watermarker.embed(content, "101")
    print(f"水印后: {watermarked}")
    detect_result = watermarker.detect(watermarked)
    print(f"水印检测: {detect_result}")

    # 4. 审计日志链
    print(f"\n--- 4. 审计日志链 ---")
    queries = [
        ("u1", "退货流程是什么？", "退货需要先提交申请..."),
        ("u2", "产品价格多少？", "基础版99元/月..."),
        ("u3", "如何联系客服？", "您可以拨打400电话..."),
    ]
    for user_id, query, answer in queries:
        resp = signer.sign(answer, {"user_id": user_id})
        audit.log(resp, user_id, query)

    chain_result = audit.verify_chain()
    print(f"日志链验证: {'✅ 完整' if chain_result['valid'] else '❌ 被篡改'}")
    print(f"总记录数: {chain_result.get('total_entries', 0)}")

    for log in audit.logs:
        print(f"  #{log['sequence']} user={log['user_id']} resp={log['response_id']}")


if __name__ == "__main__":
    main()
