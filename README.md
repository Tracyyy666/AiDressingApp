## 🔌 API 接口约定 (数据协议)

为了确保前后端顺利对接，我们约定通过 `/get_advice` 接口进行数据交换。

### 1. 发送请求 (Frontend -> Backend)
**请求方式**: `POST`
**数据格式 (JSON)**:
```json
{
    "height": 170,          // 数字类型，单位 cm
    "weight": 60,           // 数字类型，单位 kg
    "body_shape": "pear",   // 字符串：pear/apple/hourglass/rectangle/inverted_triangle
    "styles": ["casual"],   // 数组：用户勾选的风格标签列表
    "color_tone": "cool",   // (可选) 肤色调性：cool/warm/neutral
    "special_needs": ""     // (可选) 用户的个性化补充描述
}