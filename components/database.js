const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bcrypt = require('bcrypt');

const db = new sqlite3.Database(path.join(__dirname, '..', 'database.sqlite'));

// 初始化数据库表
const initDatabase = () => {
    db.serialize(() => {
        // 用户表
        db.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);

        // 权限表
        db.run(`CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )`);

        // 角色权限关联表
        db.run(`CREATE TABLE IF NOT EXISTS role_permissions (
            role TEXT NOT NULL,
            permission_id INTEGER NOT NULL,
            FOREIGN KEY (permission_id) REFERENCES permissions (id)
        )`);
    });
};

initDatabase();

module.exports = db;
