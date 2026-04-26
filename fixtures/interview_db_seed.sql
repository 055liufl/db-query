-- interview_db: 公司招聘面试管理系统
-- 目标数据库: MySQL
-- 执行方式:
--   mysql -u root -p < fixtures/interview_db_seed.sql
--   或: mysql -u root -h 127.0.0.1 -P 3306 < fixtures/interview_db_seed.sql

CREATE DATABASE IF NOT EXISTS interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE interview_db;

-- ============================================================
-- 1. 部门表
-- ============================================================
DROP TABLE IF EXISTS interview_feedback;
DROP TABLE IF EXISTS interview_schedule;
DROP TABLE IF EXISTS offers;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS job_positions;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS interviewers;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    head_name VARCHAR(80) COMMENT '部门负责人姓名',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO departments (id, name, head_name, created_at) VALUES
(1,  '工程部',       '张伟',   '2024-01-10 09:00:00'),
(2,  '产品部',       '李娜',   '2024-01-10 09:00:00'),
(3,  '设计部',       '王芳',   '2024-02-01 10:00:00'),
(4,  '市场部',       '赵磊',   '2024-02-15 10:00:00'),
(5,  '人力资源部',   '孙秀英', '2024-03-01 09:30:00'),
(6,  '财务部',       '周敏',   '2024-03-01 09:30:00'),
(7,  '数据部',       '吴强',   '2024-04-01 08:00:00'),
(8,  '运营部',       '郑丽',   '2024-05-01 08:00:00');

-- ============================================================
-- 2. 面试官表
-- ============================================================
CREATE TABLE interviewers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(150) NOT NULL,
    title VARCHAR(100) COMMENT '职位头衔',
    department_id INT NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

INSERT INTO interviewers (id, name, email, title, department_id, is_active, created_at) VALUES
(1,  '张伟',   'zhang.wei@company.com',     '工程总监',         1, 1, '2024-01-15 09:00:00'),
(2,  '陈明',   'chen.ming@company.com',     '高级后端工程师',   1, 1, '2024-01-15 09:00:00'),
(3,  '刘洋',   'liu.yang@company.com',      '前端技术负责人',   1, 1, '2024-01-20 09:00:00'),
(4,  '李娜',   'li.na@company.com',         '产品总监',         2, 1, '2024-01-20 09:00:00'),
(5,  '王芳',   'wang.fang@company.com',     '设计总监',         3, 1, '2024-02-05 09:00:00'),
(6,  '赵磊',   'zhao.lei@company.com',      '市场总监',         4, 1, '2024-02-20 09:00:00'),
(7,  '孙秀英', 'sun.xiuying@company.com',   'HR 总监',          5, 1, '2024-03-05 09:00:00'),
(8,  '吴强',   'wu.qiang@company.com',      '数据架构师',       7, 1, '2024-04-05 09:00:00'),
(9,  '黄磊',   'huang.lei@company.com',     '高级算法工程师',   7, 1, '2024-04-10 09:00:00'),
(10, '林小燕', 'lin.xiaoyan@company.com',   '资深产品经理',     2, 1, '2024-05-01 09:00:00'),
(11, '周敏',   'zhou.min@company.com',      '财务总监',         6, 1, '2024-03-05 09:00:00'),
(12, '郑丽',   'zheng.li@company.com',      '运营总监',         8, 1, '2024-05-05 09:00:00'),
(13, '何涛',   'he.tao@company.com',        '高级全栈工程师',   1, 0, '2024-02-01 09:00:00'),
(14, '马超',   'ma.chao@company.com',       'DevOps 负责人',    1, 1, '2024-06-01 09:00:00');

-- ============================================================
-- 3. 职位表
-- ============================================================
CREATE TABLE job_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    department_id INT NOT NULL,
    level ENUM('junior','mid','senior','lead','manager','director') NOT NULL DEFAULT 'mid',
    salary_min DECIMAL(10,2) COMMENT '月薪下限 (元)',
    salary_max DECIMAL(10,2) COMMENT '月薪上限 (元)',
    headcount INT NOT NULL DEFAULT 1 COMMENT '招聘人数',
    status ENUM('open','paused','filled','cancelled') NOT NULL DEFAULT 'open',
    description TEXT,
    requirements TEXT,
    location VARCHAR(100) DEFAULT '北京',
    is_remote TINYINT(1) NOT NULL DEFAULT 0,
    published_at DATETIME,
    closed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

INSERT INTO job_positions (id, title, department_id, level, salary_min, salary_max, headcount, status, description, requirements, location, is_remote, published_at, closed_at) VALUES
(1,  '高级后端工程师',       1, 'senior',   30000, 50000, 2, 'open',
     '负责核心业务系统的设计与开发，参与技术方案评审，指导初中级工程师。',
     '5年以上 Java/Go/Python 后端开发经验；熟悉微服务架构；熟悉 MySQL、Redis、Kafka。',
     '北京', 0, '2025-09-01 10:00:00', NULL),
(2,  '前端工程师',           1, 'mid',      20000, 35000, 3, 'open',
     '负责 Web 前端开发，与产品、设计紧密配合，优化用户体验。',
     '3年以上前端开发经验；精通 React/Vue；了解 TypeScript；有移动端适配经验优先。',
     '北京', 1, '2025-09-15 10:00:00', NULL),
(3,  '产品经理',             2, 'senior',   28000, 45000, 1, 'open',
     '主导产品规划与需求分析，跟进产品迭代，推动跨部门协作。',
     '5年以上互联网产品经验；有 B 端 SaaS 产品经验优先；出色的沟通与项目管理能力。',
     '上海', 0, '2025-10-01 10:00:00', NULL),
(4,  'UI/UX 设计师',         3, 'mid',      18000, 32000, 1, 'filled',
     '负责产品交互与视觉设计，制定设计规范，输出高保真原型。',
     '3年以上 UI/UX 设计经验；熟练使用 Figma/Sketch；有设计系统构建经验优先。',
     '北京', 0, '2025-08-01 10:00:00', '2025-12-20 17:00:00'),
(5,  '市场专员',             4, 'junior',   12000, 18000, 2, 'open',
     '执行线上线下市场活动，撰写营销内容，分析推广效果。',
     '1年以上市场或运营经验；熟悉社交媒体运营；有数据分析意识。',
     '深圳', 0, '2025-11-01 10:00:00', NULL),
(6,  'HRBP',                 5, 'senior',   25000, 40000, 1, 'paused',
     '深入业务部门提供人力资源解决方案，推动组织发展与人才梯队建设。',
     '5年以上 HR 经验，至少 2 年 HRBP 经验；了解劳动法规；优秀的沟通能力。',
     '北京', 0, '2025-10-15 10:00:00', NULL),
(7,  '数据工程师',           7, 'mid',      25000, 40000, 2, 'open',
     '构建和维护数据管道，保障数据质量，支持数据分析与 AI 团队。',
     '3年以上数据开发经验；熟悉 Spark/Flink；精通 SQL；了解数据仓库建模。',
     '杭州', 1, '2025-11-15 10:00:00', NULL),
(8,  '算法工程师',           7, 'senior',   35000, 55000, 1, 'open',
     '研发推荐/搜索/NLP 算法模型，推动模型线上化与效果优化。',
     '硕士及以上学历；3年以上算法工程化经验；熟悉 PyTorch/TensorFlow；有论文发表优先。',
     '北京', 0, '2025-12-01 10:00:00', NULL),
(9,  '运营经理',             8, 'lead',     28000, 42000, 1, 'open',
     '制定运营策略，负责用户增长与留存，管理运营团队日常工作。',
     '5年以上互联网运营经验；有团队管理经验；擅长数据驱动决策。',
     '上海', 0, '2026-01-10 10:00:00', NULL),
(10, 'DevOps 工程师',        1, 'mid',      22000, 38000, 1, 'cancelled',
     '负责 CI/CD 流水线建设，容器化部署与监控告警体系搭建。',
     '3年以上 DevOps 经验；熟悉 Kubernetes、Docker、Terraform；有 AWS/阿里云经验。',
     '北京', 1, '2025-07-01 10:00:00', '2025-09-30 17:00:00');

-- ============================================================
-- 4. 候选人表
-- ============================================================
CREATE TABLE candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    gender ENUM('male','female','other') DEFAULT NULL,
    birth_date DATE,
    education ENUM('high_school','bachelor','master','phd') DEFAULT 'bachelor',
    university VARCHAR(150),
    major VARCHAR(100),
    years_of_experience DECIMAL(3,1) DEFAULT 0.0,
    current_company VARCHAR(150),
    current_title VARCHAR(100),
    expected_salary DECIMAL(10,2) COMMENT '期望月薪 (元)',
    resume_url VARCHAR(500),
    source ENUM('lagou','boss','linkedin','referral','campus','official_site','other') DEFAULT 'other',
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO candidates (id, name, email, phone, gender, birth_date, education, university, major, years_of_experience, current_company, current_title, expected_salary, resume_url, source, notes) VALUES
(1,  '李明',     'liming@gmail.com',         '13800001001', 'male',   '1993-05-12', 'master',   '北京大学',       '计算机科学',     8.0,  '字节跳动',   '高级后端工程师',   45000, 'https://resumes.example.com/liming.pdf',      'boss',          '技术能力突出，有大规模分布式系统经验'),
(2,  '王丽华',   'wanglihua@qq.com',         '13900002002', 'female', '1996-09-23', 'bachelor', '浙江大学',       '软件工程',       5.0,  '阿里巴巴',   '前端工程师',       30000, 'https://resumes.example.com/wanglihua.pdf',   'lagou',         NULL),
(3,  '陈浩',     'chenhao@outlook.com',      '13700003003', 'male',   '1991-02-08', 'master',   '清华大学',       '软件工程',       10.0, '美团',       '技术经理',         50000, 'https://resumes.example.com/chenhao.pdf',     'linkedin',      '有团队管理经验，沟通能力强'),
(4,  '赵雪',     'zhaoxue@163.com',          '13600004004', 'female', '1997-11-30', 'bachelor', '同济大学',       '视觉传达设计',   4.0,  '网易',       'UI 设计师',        28000, 'https://resumes.example.com/zhaoxue.pdf',     'boss',          '作品集质量很高'),
(5,  '孙磊',     'sunlei@gmail.com',         '13500005005', 'male',   '1994-07-19', 'master',   '上海交通大学',   '数据科学',       7.0,  '腾讯',       '数据工程师',       38000, 'https://resumes.example.com/sunlei.pdf',      'referral',      '内推，由数据部吴强推荐'),
(6,  '周婷',     'zhouting@hotmail.com',     '13400006006', 'female', '1998-03-14', 'bachelor', '复旦大学',       '市场营销',       2.5,  '小红书',     '市场运营',         16000, 'https://resumes.example.com/zhouting.pdf',    'lagou',         NULL),
(7,  '吴昊天',   'wuhaotian@gmail.com',      '13300007007', 'male',   '1995-12-01', 'phd',      '中国科学技术大学','机器学习',       5.0,  '百度',       '算法工程师',       50000, 'https://resumes.example.com/wuhaotian.pdf',   'linkedin',      '有 3 篇顶会论文，擅长 NLP'),
(8,  '郑雅文',   'zhengyawen@qq.com',        '13200008008', 'female', '1992-08-25', 'master',   '南京大学',       '工商管理',       9.0,  '京东',       '高级产品经理',     42000, 'https://resumes.example.com/zhengyawen.pdf',  'referral',      '内推，产品思维清晰'),
(9,  '刘志强',   'liuzhiqiang@163.com',      '13100009009', 'male',   '1990-01-07', 'bachelor', '华中科技大学',   '人力资源管理',   11.0, '滴滴',       'HRBP',             38000, 'https://resumes.example.com/liuzhiqiang.pdf', 'official_site', '有丰富的 HRBP 经验'),
(10, '黄晓峰',   'huangxiaofeng@gmail.com',  '13000010010', 'male',   '1996-04-18', 'master',   '哈尔滨工业大学', '计算机科学',     5.5,  '华为',       '后端工程师',       35000, 'https://resumes.example.com/huangxiaofeng.pdf','campus',        '校招转正，华为工作 5 年'),
(11, '林雨欣',   'linyuxin@qq.com',          '13800011011', 'female', '1999-06-22', 'bachelor', '中山大学',       '传播学',         1.5,  '快手',       '内容运营',         15000, 'https://resumes.example.com/linyuxin.pdf',    'boss',          NULL),
(12, '许志远',   'xuzhiyuan@outlook.com',    '13700012012', 'male',   '1993-10-09', 'master',   '武汉大学',       '统计学',         7.5,  '蚂蚁金服',   '数据分析师',       40000, 'https://resumes.example.com/xuzhiyuan.pdf',   'lagou',         '有很强的数据建模能力'),
(13, '杨佳',     'yangjia@gmail.com',        '13600013013', 'female', '1997-01-15', 'bachelor', '东南大学',       '软件工程',       4.0,  '携程',       '前端工程师',       26000, 'https://resumes.example.com/yangjia.pdf',     'boss',          NULL),
(14, '何明',     'heming@163.com',           '13500014014', 'male',   '1994-08-30', 'master',   '北京航空航天大学','计算机科学',     6.5,  'OPPO',       '全栈工程师',       32000, 'https://resumes.example.com/heming.pdf',      'referral',      '何涛内推的前同事'),
(15, '谢芳',     'xiefang@hotmail.com',      '13400015015', 'female', '1995-05-20', 'master',   '西安交通大学',   '运营管理',       6.0,  '拼多多',     '运营主管',         35000, 'https://resumes.example.com/xiefang.pdf',     'linkedin',      '有用户增长与留存经验'),
(16, '高远',     'gaoyuan@gmail.com',        '13300016016', 'male',   '2000-02-28', 'bachelor', '厦门大学',       '前端开发',       2.0,  '字节跳动',   '前端工程师',       22000, 'https://resumes.example.com/gaoyuan.pdf',     'campus',        '应届表现优秀，学习能力强'),
(17, '马丽萍',   'maliping@qq.com',          '13200017017', 'female', '1991-11-11', 'bachelor', '四川大学',       '人力资源管理',   12.0, '美团',       'HR 经理',          36000, 'https://resumes.example.com/maliping.pdf',    'official_site', NULL),
(18, '罗峰',     'luofeng@outlook.com',      '13100018018', 'male',   '1988-07-04', 'phd',      '中科院计算所',   '自然语言处理',   10.0, '微软亚洲研究院','研究员',          55000, 'https://resumes.example.com/luofeng.pdf',     'linkedin',      '资深 NLP 研究者，发表论文 10 余篇');

-- ============================================================
-- 5. 投递/申请表
-- ============================================================
CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    position_id INT NOT NULL,
    status ENUM('pending','screening','interviewing','offered','accepted','rejected','withdrawn') NOT NULL DEFAULT 'pending',
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    rejection_reason VARCHAR(300),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    FOREIGN KEY (position_id) REFERENCES job_positions(id)
) ENGINE=InnoDB;

INSERT INTO applications (id, candidate_id, position_id, status, applied_at, rejection_reason) VALUES
-- 高级后端工程师 (position 1)
(1,  1,  1, 'offered',       '2025-09-10 14:00:00', NULL),
(2,  3,  1, 'interviewing',  '2025-09-12 11:00:00', NULL),
(3,  10, 1, 'interviewing',  '2025-10-05 09:00:00', NULL),
(4,  14, 1, 'rejected',      '2025-10-08 16:00:00', '技术深度不足，系统设计环节表现较弱'),
-- 前端工程师 (position 2)
(5,  2,  2, 'accepted',      '2025-09-20 10:00:00', NULL),
(6,  13, 2, 'interviewing',  '2025-10-01 09:30:00', NULL),
(7,  16, 2, 'screening',     '2025-11-20 15:00:00', NULL),
-- 产品经理 (position 3)
(8,  8,  3, 'interviewing',  '2025-10-10 13:00:00', NULL),
-- UI/UX 设计师 (position 4, filled)
(9,  4,  4, 'accepted',      '2025-08-15 10:00:00', NULL),
-- 市场专员 (position 5)
(10, 6,  5, 'interviewing',  '2025-11-10 11:00:00', NULL),
(11, 11, 5, 'screening',     '2025-11-25 14:00:00', NULL),
-- HRBP (position 6, paused)
(12, 9,  6, 'pending',       '2025-10-20 09:00:00', NULL),
(13, 17, 6, 'pending',       '2025-10-25 10:00:00', NULL),
-- 数据工程师 (position 7)
(14, 5,  7, 'offered',       '2025-11-20 10:00:00', NULL),
(15, 12, 7, 'interviewing',  '2025-12-01 09:00:00', NULL),
-- 算法工程师 (position 8)
(16, 7,  8, 'interviewing',  '2025-12-10 14:00:00', NULL),
(17, 18, 8, 'interviewing',  '2025-12-15 11:00:00', NULL),
-- 运营经理 (position 9)
(18, 15, 9, 'screening',     '2026-01-15 10:00:00', NULL);

-- ============================================================
-- 6. 面试安排表
-- ============================================================
CREATE TABLE interview_schedule (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    round TINYINT NOT NULL COMMENT '面试轮次: 1=初筛, 2=技术面, 3=主管面, 4=HR 面, 5=终面',
    interviewer_id INT NOT NULL,
    scheduled_at DATETIME NOT NULL COMMENT '面试时间',
    duration_minutes INT NOT NULL DEFAULT 60,
    location VARCHAR(200) COMMENT '面试地点或会议链接',
    interview_type ENUM('phone','video','onsite') NOT NULL DEFAULT 'video',
    status ENUM('scheduled','completed','cancelled','no_show') NOT NULL DEFAULT 'scheduled',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (interviewer_id) REFERENCES interviewers(id)
) ENGINE=InnoDB;

INSERT INTO interview_schedule (id, application_id, round, interviewer_id, scheduled_at, duration_minutes, location, interview_type, status) VALUES
-- 李明 -> 高级后端 (app 1): 已完成全部面试
(1,  1, 1, 7,  '2025-09-15 10:00:00', 30,  '腾讯会议 #8001', 'phone',  'completed'),
(2,  1, 2, 2,  '2025-09-18 14:00:00', 60,  '腾讯会议 #8002', 'video',  'completed'),
(3,  1, 3, 1,  '2025-09-22 10:00:00', 60,  '公司 A 栋 3 楼会议室', 'onsite', 'completed'),
(4,  1, 4, 7,  '2025-09-25 15:00:00', 45,  '腾讯会议 #8003', 'video',  'completed'),
-- 陈浩 -> 高级后端 (app 2): 已完成两轮
(5,  2, 1, 7,  '2025-09-16 14:00:00', 30,  '腾讯会议 #8004', 'phone',  'completed'),
(6,  2, 2, 2,  '2025-09-20 10:00:00', 60,  '腾讯会议 #8005', 'video',  'completed'),
(7,  2, 3, 1,  '2025-10-15 14:00:00', 60,  '公司 A 栋 3 楼会议室', 'onsite', 'scheduled'),
-- 黄晓峰 -> 高级后端 (app 3): 技术面进行中
(8,  3, 1, 7,  '2025-10-10 10:00:00', 30,  '腾讯会议 #8006', 'phone',  'completed'),
(9,  3, 2, 14, '2025-10-18 14:00:00', 60,  '腾讯会议 #8007', 'video',  'scheduled'),
-- 何明 -> 高级后端 (app 4): 被拒
(10, 4, 1, 7,  '2025-10-12 11:00:00', 30,  '腾讯会议 #8008', 'phone',  'completed'),
(11, 4, 2, 2,  '2025-10-16 14:00:00', 60,  '腾讯会议 #8009', 'video',  'completed'),
-- 王丽华 -> 前端 (app 5): 已接受 offer
(12, 5, 1, 7,  '2025-09-25 10:00:00', 30,  '腾讯会议 #8010', 'phone',  'completed'),
(13, 5, 2, 3,  '2025-09-28 14:00:00', 60,  '腾讯会议 #8011', 'video',  'completed'),
(14, 5, 3, 1,  '2025-10-02 10:00:00', 60,  '公司 A 栋 3 楼会议室', 'onsite', 'completed'),
(15, 5, 4, 7,  '2025-10-05 15:00:00', 45,  '腾讯会议 #8012', 'video',  'completed'),
-- 杨佳 -> 前端 (app 6): 技术面完成
(16, 6, 1, 7,  '2025-10-05 10:00:00', 30,  '腾讯会议 #8013', 'phone',  'completed'),
(17, 6, 2, 3,  '2025-10-10 14:00:00', 60,  '腾讯会议 #8014', 'video',  'completed'),
(18, 6, 3, 1,  '2025-10-20 10:00:00', 60,  '公司 A 栋 3 楼会议室', 'onsite', 'scheduled'),
-- 郑雅文 -> 产品经理 (app 8)
(19, 8, 1, 7,  '2025-10-15 10:00:00', 30,  '腾讯会议 #8015', 'phone',  'completed'),
(20, 8, 2, 10, '2025-10-20 14:00:00', 60,  '腾讯会议 #8016', 'video',  'completed'),
(21, 8, 3, 4,  '2025-10-28 10:00:00', 60,  '公司 B 栋 5 楼会议室', 'onsite', 'scheduled'),
-- 赵雪 -> UI/UX (app 9): 全部完成并入职
(22, 9, 1, 7,  '2025-08-20 10:00:00', 30,  '腾讯会议 #8017', 'phone',  'completed'),
(23, 9, 2, 5,  '2025-08-25 14:00:00', 60,  '腾讯会议 #8018', 'video',  'completed'),
(24, 9, 3, 5,  '2025-09-01 10:00:00', 45,  '公司 A 栋 2 楼设计室', 'onsite', 'completed'),
(25, 9, 4, 7,  '2025-09-05 15:00:00', 45,  '腾讯会议 #8019', 'video',  'completed'),
-- 周婷 -> 市场专员 (app 10)
(26, 10, 1, 7,  '2025-11-15 10:00:00', 30,  '腾讯会议 #8020', 'phone', 'completed'),
(27, 10, 2, 6,  '2025-11-20 14:00:00', 45,  '腾讯会议 #8021', 'video', 'completed'),
(28, 10, 3, 6,  '2025-12-01 10:00:00', 45,  '公司 C 栋 2 楼会议室', 'onsite', 'scheduled'),
-- 孙磊 -> 数据工程师 (app 14): 全部完成
(29, 14, 1, 7,  '2025-11-25 10:00:00', 30,  '腾讯会议 #8022', 'phone', 'completed'),
(30, 14, 2, 8,  '2025-11-28 14:00:00', 60,  '腾讯会议 #8023', 'video', 'completed'),
(31, 14, 3, 8,  '2025-12-05 10:00:00', 60,  '公司 D 栋 4 楼会议室', 'onsite', 'completed'),
(32, 14, 4, 7,  '2025-12-10 15:00:00', 45,  '腾讯会议 #8024', 'video', 'completed'),
-- 许志远 -> 数据工程师 (app 15)
(33, 15, 1, 7,  '2025-12-05 10:00:00', 30,  '腾讯会议 #8025', 'phone', 'completed'),
(34, 15, 2, 9,  '2025-12-10 14:00:00', 60,  '腾讯会议 #8026', 'video', 'completed'),
(35, 15, 3, 8,  '2025-12-18 10:00:00', 60,  '公司 D 栋 4 楼会议室', 'onsite', 'scheduled'),
-- 吴昊天 -> 算法工程师 (app 16)
(36, 16, 1, 7,  '2025-12-15 10:00:00', 30,  '腾讯会议 #8027', 'phone', 'completed'),
(37, 16, 2, 9,  '2025-12-20 14:00:00', 60,  '腾讯会议 #8028', 'video', 'completed'),
(38, 16, 3, 8,  '2026-01-08 10:00:00', 60,  '公司 D 栋 4 楼会议室', 'onsite', 'scheduled'),
-- 罗峰 -> 算法工程师 (app 17)
(39, 17, 1, 7,  '2025-12-18 14:00:00', 30,  '腾讯会议 #8029', 'phone', 'completed'),
(40, 17, 2, 9,  '2025-12-23 10:00:00', 60,  '腾讯会议 #8030', 'video', 'scheduled');

-- ============================================================
-- 7. 面试反馈/评价表
-- ============================================================
CREATE TABLE interview_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    rating TINYINT NOT NULL COMMENT '1-5 分评分',
    recommendation ENUM('strong_hire','hire','neutral','no_hire','strong_no_hire') NOT NULL,
    technical_score TINYINT COMMENT '技术能力 1-5',
    communication_score TINYINT COMMENT '沟通表达 1-5',
    culture_fit_score TINYINT COMMENT '文化匹配 1-5',
    strengths TEXT,
    weaknesses TEXT,
    comments TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES interview_schedule(id)
) ENGINE=InnoDB;

INSERT INTO interview_feedback (id, schedule_id, rating, recommendation, technical_score, communication_score, culture_fit_score, strengths, weaknesses, comments) VALUES
-- 李明面试反馈
(1,  1,  4, 'hire',          NULL, 4, 4, '表达清晰，求职动机明确', NULL, '初筛通过，推荐进入技术面'),
(2,  2,  5, 'strong_hire',   5, 4, 4, '分布式系统设计能力很强，对 Kafka、Redis 原理理解深入，代码风格规范', '英语表达一般', '强烈推荐，技术能力 top 10% 候选人'),
(3,  3,  4, 'hire',          4, 4, 5, '系统设计思路清晰，有全局视野，团队协作意识强', '对业务理解需要加强', '推荐录用，可胜任高级工程师角色'),
(4,  4,  4, 'hire',          NULL, 4, 4, '职业规划清晰，薪资期望合理', NULL, 'HR 面通过，薪资可谈'),
-- 陈浩面试反馈
(5,  5,  4, 'hire',          NULL, 5, 4, '沟通非常流畅，经历丰富', NULL, '初筛通过'),
(6,  6,  4, 'hire',          4, 5, 4, '技术广度好，有管理思维，架构设计合理', '对某些底层细节不够深入', '推荐进入主管面，考虑 Tech Lead 方向'),
-- 黄晓峰面试反馈
(7,  8,  3, 'neutral',       NULL, 3, 4, '态度诚恳，有学习意愿', '表达稍显紧张', '初筛勉强通过，观察技术面表现'),
-- 何明面试反馈 (被拒)
(8,  10, 3, 'neutral',       NULL, 3, 3, '有全栈经验', '对高级职位经验不足', '勉强通过初筛'),
(9,  11, 2, 'no_hire',       2, 3, 3, '代码能力尚可', '系统设计回答较浅，缺乏大规模项目经验，对并发场景理解不足', '不建议录用高级后端岗位'),
-- 王丽华面试反馈
(10, 12, 4, 'hire',          NULL, 4, 4, '自信大方，目标明确', NULL, '初筛通过'),
(11, 13, 5, 'strong_hire',   5, 4, 4, 'React 生态非常熟悉，性能优化经验丰富，代码质量高', '对后端知识了解较少', '强烈推荐，前端能力突出'),
(12, 14, 4, 'hire',          4, 4, 5, '有很好的工程素养和团队意识', NULL, '推荐通过'),
(13, 15, 4, 'hire',          NULL, 4, 4, '期望薪资合理，入职意愿强', NULL, 'HR 面通过，可发 offer'),
-- 杨佳面试反馈
(14, 16, 4, 'hire',          NULL, 4, 3, '态度积极', '职业规划不够清晰', '初筛通过'),
(15, 17, 3, 'neutral',       3, 3, 4, 'Vue 比较熟练', 'React 经验较少，TypeScript 使用不够深入', '建议主管面进一步考察'),
-- 郑雅文面试反馈
(16, 19, 5, 'hire',          NULL, 5, 5, '沟通极佳，产品思维敏锐', NULL, '优秀候选人，强烈推荐'),
(17, 20, 4, 'hire',          4, 5, 4, '需求分析能力强，有数据驱动产品的经验，对 B 端产品理解到位', '技术理解深度一般', '推荐进入总监面试'),
-- 赵雪面试反馈
(18, 22, 4, 'hire',          NULL, 4, 4, '热情开朗，对设计充满热忱', NULL, '初筛通过'),
(19, 23, 5, 'strong_hire',   5, 4, 5, '设计功底扎实，作品集水平很高，对设计系统有深入思考', NULL, '强烈推荐'),
(20, 24, 4, 'hire',          4, 4, 5, '设计理念与团队方向一致', '动效设计经验偏少', '推荐录用'),
(21, 25, 4, 'hire',          NULL, 4, 5, '文化匹配度高，薪资合理', NULL, 'HR 面通过'),
-- 周婷面试反馈
(22, 26, 3, 'neutral',       NULL, 4, 3, '有活力，学习意愿强', '经验偏少', '初筛通过，需要在后续面试中进一步评估'),
(23, 27, 4, 'hire',          3, 4, 4, '市场感觉不错，有创意', '数据分析能力待提升', '推荐继续面试'),
-- 孙磊面试反馈
(24, 29, 4, 'hire',          NULL, 4, 4, '经验丰富，表达清晰', NULL, '初筛通过'),
(25, 30, 5, 'strong_hire',   5, 4, 4, 'Spark/Flink 实战经验丰富，SQL 能力极强，对数据质量有系统性思考', NULL, '强烈推荐'),
(26, 31, 4, 'hire',          4, 4, 5, '解决问题思路清晰，能独立负责项目', '对实时计算了解稍浅', '推荐录用'),
(27, 32, 4, 'hire',          NULL, 4, 4, '入职意愿强，期望合理', NULL, 'HR 面通过，可发 offer'),
-- 许志远面试反馈
(28, 33, 4, 'hire',          NULL, 4, 4, '经历背景匹配', NULL, '初筛通过'),
(29, 34, 4, 'hire',          4, 4, 3, '数据建模能力强，SQL 水平高', '对分布式计算框架使用较少', '推荐进入主管面'),
-- 吴昊天面试反馈
(30, 36, 5, 'strong_hire',   NULL, 5, 5, '学术背景出色，沟通能力很强', NULL, '优秀候选人'),
(31, 37, 5, 'strong_hire',   5, 5, 4, '算法基础扎实，工程化能力强，有端到端模型上线经验', '团队管理经验较少', '非常优秀，强烈推荐'),
-- 罗峰面试反馈
(32, 39, 5, 'strong_hire',   NULL, 5, 4, '资深 NLP 研究背景，沟通清晰', NULL, '非常优秀的候选人');

-- ============================================================
-- 8. Offer 表
-- ============================================================
CREATE TABLE offers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    offered_salary DECIMAL(10,2) NOT NULL COMMENT '实际 offer 月薪 (元)',
    bonus VARCHAR(200) COMMENT '签字费或其他奖金',
    stock_options VARCHAR(200) COMMENT '期权/股权信息',
    start_date DATE NOT NULL COMMENT '预计入职日期',
    expiry_date DATE NOT NULL COMMENT 'Offer 有效期',
    status ENUM('pending','accepted','declined','expired','revoked') NOT NULL DEFAULT 'pending',
    decline_reason VARCHAR(300),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id)
) ENGINE=InnoDB;

INSERT INTO offers (id, application_id, offered_salary, bonus, stock_options, start_date, expiry_date, status, decline_reason) VALUES
(1, 1,  45000, '签字费 30,000 元',   '期权 20,000 股，4 年 vesting', '2025-11-01', '2025-10-15', 'accepted', NULL),
(2, 5,  28000, NULL,                  '期权 8,000 股，4 年 vesting',  '2025-11-15', '2025-10-20', 'accepted', NULL),
(3, 9,  27000, '签字费 10,000 元',   NULL,                            '2025-10-15', '2025-09-25', 'accepted', NULL),
(4, 14, 36000, '签字费 20,000 元',   '期权 15,000 股，4 年 vesting', '2026-01-15', '2026-01-01', 'pending',  NULL);
