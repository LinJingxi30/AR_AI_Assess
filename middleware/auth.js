const jwt = require('jsonwebtoken');
const db = require('../models/database');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// 认证中间件
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) return res.status(401).json({ error: '未提供身份验证令牌' });

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) return res.status(403).json({ error: '令牌无效' });
        req.user = user;
        next();
    });
};

// 权限验证中间件
const checkPermission = (requiredPermission) => {
    return (req, res, next) => {
        const userRole = req.user.role;
        
        db.get(
            `SELECT COUNT(*) as count FROM role_permissions rp 
             JOIN permissions p ON rp.permission_id = p.id 
             WHERE rp.role = ? AND p.name = ?`,
            [userRole, requiredPermission],
            (err, row) => {
                if (err) return res.status(500).json({ error: '服务器错误' });
                if (row.count === 0) return res.status(403).json({ error: '权限不足' });
                next();
            }
        );
    };
};

module.exports = { authenticateToken, checkPermission };
