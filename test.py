CREATE TABLE `bd_gps_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `geohash` varchar(10) NOT NULL COMMENT 'geohash',
  `reg_7d_dam_cust_num` int(11) DEFAULT '0' COMMENT '注册近7天十米GPS关联客户数(gps4位)',
  `reg_30d_dam_cust_num` int(11) DEFAULT '0' COMMENT '注册近30天十米GPS关联客户数(gps4位)',
  `crdt_7d_dam_cust_num` int(11) DEFAULT '0' COMMENT '授信近7天十米GPS关联客户数(gps4位)',
  `crdt_30d_dam_cust_num` int(11) DEFAULT '0' COMMENT '授信近30天十米GPS关联客户数(gps4位)',
  `lttr_7d_dam_cust_num` int(11) DEFAULT '0' COMMENT '用信近7天十米GPS关联客户数(gps4位)',
  `lttr_30d_dam_cust_num` int(11) DEFAULT '0' COMMENT '用信近30天十米GPS关联客户数(gps4位)',
  `reg_7d_hm_cust_num` int(11) DEFAULT '0' COMMENT '注册近7天百米GPS关联客户数(gps3位)',
  `reg_30d_hm_cust_num` int(11) DEFAULT '0' COMMENT '注册近30天百米GPS关联客户数(gps3位)',
  PRIMARY KEY (`data_date`,`geohash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='GPS变量标签';

CREATE TABLE `bd_ip_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `usr_ipaddr` varchar(50) NOT NULL COMMENT '用户ip地址',
  `reg_3d_cust_num` int(11) DEFAULT '0' COMMENT '注册近3天IP关联客户数',
  `reg_7d_cust_num` int(11) DEFAULT '0' COMMENT '注册近7天IP关联客户数',
  `reg_30d_cust_num` int(11) DEFAULT '0' COMMENT '注册近30天IP关联客户数',
  `lttr_3d_cust_num` int(11) DEFAULT '0' COMMENT '用信近3天IP关联客户数',
  `lttr_7d_cust_num` int(11) DEFAULT '0' COMMENT '用信近7天IP关联客户数',
  `lttr_30d_cust_num` int(11) DEFAULT '0' COMMENT '用信近30天IP关联客户数',
  PRIMARY KEY (`data_date`, `usr_ipaddr`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='IP变量标签';

CREATE TABLE `bd_openid_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `open_id` varchar(50) NOT NULL COMMENT 'OPEN_ID',
  `reg_3d_tlphn_num` int(11) DEFAULT '0' COMMENT '注册近3天关联手机号码数',
  `reg_7d_tlphn_num` int(11) DEFAULT '0' COMMENT '注册近7天关联手机号码数',
  `reg_30d_tlphn_num` int(11) DEFAULT '0' COMMENT '注册近30天关联手机号码数',
  PRIMARY KEY (`data_date`, `open_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='OPENID变量标签';


CREATE TABLE `bd_wifi_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `wifi_mac_addr` varchar(50) NOT NULL COMMENT 'wifi mac地址（路由器）',
  `crdt_3d_cust_num` int(11) DEFAULT '0' COMMENT '授信近3天WIFI关联客户数',
  `crdt_7d_cust_num` int(11) DEFAULT '0' COMMENT '授信近7天WIFI关联客户数',
  `crdt_30d_cust_num` int(11) DEFAULT '0' COMMENT '授信近30天WIFI关联客户数',
  `lttr_3d_cust_num` int(11) DEFAULT '0' COMMENT '用信近3天WIFI关联客户数',
  `lttr_7d_cust_num` int(11) DEFAULT '0' COMMENT '用信近7天WIFI关联客户数',
  `lttr_30d_cust_num` int(11) DEFAULT '0' COMMENT '用信近30天WIFI关联客户数',
  PRIMARY KEY (`data_date`, `wifi_mac_addr`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='WIFI变量标签';

CREATE TABLE `bd_rsrn_addr_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `rsrn_addr` varchar(50) NOT NULL COMMENT '户籍地址',
  `lttr_3d_cust_num` int(11) DEFAULT '0' COMMENT '用信近3天户籍地址关联客户数',
  `lttr_7d_cust_num` int(11) DEFAULT '0' COMMENT '用信近7天户籍地址关联客户数',
  `lttr_30d_cust_num` int(11) DEFAULT '0' COMMENT '用信近30天户籍地址关联客户数',
  PRIMARY KEY (`data_date`, `rsrn_addr`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='户籍地址变量标签';

CREATE TABLE `bd_usr_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `usr_no` varchar(200) NOT NULL COMMENT '用户编号',
  `nr_1m_mdfy_phn_num` int(11) DEFAULT '0' COMMENT '近1月修改注册手机号码次数',
  `nr_3m_mdfy_phn_num` int(11) DEFAULT '0' COMMENT '近3月修改注册手机号码次数',
  `nr_6m_mdfy_phn_num` int(11) DEFAULT '0' COMMENT '近6月修改注册手机号码次数',
  `nr_12m_mdfy_phn_num` int(11) DEFAULT '0' COMMENT '近12月修改注册手机号码次数',
  `nr_7d_mdfy_psr_num` int(11) DEFAULT '0' COMMENT '近7天账户修改交易密码数',
  `nr_30d_mdfy_psr_num` int(11) DEFAULT '0' COMMENT '近30天账户修改交易密码数',
  `nr_7d_rlt_fgpn_num` int(11) DEFAULT '0' COMMENT '近7天关联不同简易设备指纹数',
  `nr_30d_rlt_fgpn_num` int(11) DEFAULT '0' COMMENT '近30天关联不同简易设备指纹数',
  `crdt_3d_scr_num` int(11) DEFAULT '0' COMMENT '授信近3天截屏次数',
  `crdt_3d_exit_prgrm_num` int(11) DEFAULT '0' COMMENT '授信近3天跳出小程序次数',
  `lttr_3d_scr_num` int(11) DEFAULT '0' COMMENT '用信近3天截屏次数',
  `lttr_3d_exit_prgrm_num` int(11) DEFAULT '0' COMMENT '用信近3天跳出小程序次数',
  PRIMARY KEY (`data_date`, `usr_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户变量标签';CREATE TABLE `bd_tlphn_lbl_pl` (
  `data_date` varchar(10) NOT NULL COMMENT '数据日期',
  `cr_cust_no` varchar(50) NOT NULL COMMENT '核心客户号',
  
  -- [上半部分字段 3-28]
  `mbl_phn` varchar(30) DEFAULT NULL COMMENT '手机号码',
  `crrnt_ovd_stts` varchar(5) DEFAULT NULL COMMENT '当前逾期状态',
  `crrnt_ovd_num` int(11) DEFAULT '0' COMMENT '当前逾期笔数',
  `crrnt_ovd_amt` decimal(18,2) DEFAULT '0.00' COMMENT '当前逾期金额',
  `crrnt_noclr_ets_num` int(11) DEFAULT '0' COMMENT '当前未结清延期笔数',
  `crrnt_noclr_ets_amt` decimal(18,2) DEFAULT '0.00' COMMENT '当前未结清延期金额',
  `crrnt_lumpsum_cpsn_num` int(11) DEFAULT '0' COMMENT '当前整笔代偿笔数',
  `crrnt_lumpsum_cpsn_amt` decimal(18,2) DEFAULT '0.00' COMMENT '当前整笔代偿金额',
  `his_max_ovd_dys` int(11) DEFAULT '0' COMMENT '历史最大逾期天数',
  `ant_mnylaun_bclt_flg` varchar(5) DEFAULT NULL COMMENT '反洗钱黑名单标志',
  `ant_mnylaun_rsk_grd` varchar(10) DEFAULT NULL COMMENT '反洗钱风险等级',
  `bnk_crd_frz_flg` varchar(5) DEFAULT NULL COMMENT '银行卡冻结标志',
  `apply_id_no_num` int(11) DEFAULT '0' COMMENT '申请身份证号数',
  `nr_7day_apply_id_no_num` int(11) DEFAULT '0' COMMENT '近7天申请身份证号数',
  `rcnt_apply_sccss_dt` varchar(10) DEFAULT NULL COMMENT '最近申请成功日期',
  `rlt_crrnt_ovd_stts` varchar(5) DEFAULT NULL COMMENT '关联当前逾期状态',
  `rlt_crrnt_ovd_num` int(11) DEFAULT '0' COMMENT '关联当前逾期笔数',
  `rlt_crrnt_ovd_amt` decimal(18,2) DEFAULT '0.00' COMMENT '关联当前逾期金额',
  `rlt_crrnt_noclr_ets_num` int(11) DEFAULT '0' COMMENT '关联当前未结清延期笔数',
  `rlt_crrnt_noclr_ets_amt` decimal(18,2) DEFAULT '0.00' COMMENT '关联当前未结清延期金额',
  `rlt_lumpsum_cpsn_num` int(11) DEFAULT '0' COMMENT '关联当前整笔代偿笔数',
  `rlt_lumpsum_cpsn_amt` decimal(18,2) DEFAULT '0.00' COMMENT '关联当前整笔代偿金额',
  `rlt_his_max_ovd_dys` int(11) DEFAULT '0' COMMENT '关联历史最大逾期天数',
  `rlt_rcnt_apply_sccss_dt` varchar(10) DEFAULT NULL COMMENT '关联最近申请成功日期',
  `rlt_3mm_tlphn_num` int(11) DEFAULT '0' COMMENT '关联近3月手机号数',
  `nr_7day_cust_num` int(11) DEFAULT '0' COMMENT '近7天客户数',

  -- [新补充字段 29-39]
  `nr_1mm_cust_num` int(11) DEFAULT '0' COMMENT '近1月客户数',
  `nr_3mm_cust_num` int(11) DEFAULT '0' COMMENT '近3月客户数',
  `nr_6mm_cust_num` int(11) DEFAULT '0' COMMENT '近6月客户数',
  `nr_12mm_cust_num` int(11) DEFAULT '0' COMMENT '近12月客户数',
  `nr_12mm_wnd_bclt_cust_num` int(11) DEFAULT '0' COMMENT '近12月风控黑名单客户数',
  `rlt_nr_7day_cust_num` int(11) DEFAULT '0' COMMENT '关联近7天客户数',
  `rlt_nr_1mm_cust_num` int(11) DEFAULT '0' COMMENT '关联近1月客户数',
  `rlt_nr_3mm_cust_num` int(11) DEFAULT '0' COMMENT '关联近3月客户数',
  `rlt_nr_6mm_cust_num` int(11) DEFAULT '0' COMMENT '关联近6月客户数',
  `rlt_nr_12mm_cust_num` int(11) DEFAULT '0' COMMENT '关联近12月客户数',
  `rlt_nr_12mm_dfn_nm_cust_num` int(11) DEFAULT '0' COMMENT '关联近12月不同名客户数',
  
  PRIMARY KEY (`data_date`, `cr_cust_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='外脑策略手机号变量标签';
