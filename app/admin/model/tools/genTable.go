package tools

import (
	"github.com/x-thooh/thooh-admin/app/core/utils"
)

type GenTable struct {
	TableId        int64          `json:"tableId" gorm:"primaryKey;column:id"`
	Table_Name     string         `json:"tableName,omitempty" gorm:"column:name"`
	TableComment   string         `json:"tableComment" gorm:"column:notes"`
	SubTableName   string         `json:"subTableName" gorm:"-"`
	SubTableFkName string         `json:"subTableFkName" gorm:"-"`
	ClassName      string         `json:"className" gorm:"-"`
	TplCategory    string         `json:"tplCategory" gorm:"-"`
	PackageName    string         `json:"packageName" gorm:"column:panam"`
	ModuleName     string         `json:"moduleName" gorm:"-"`
	BusinessName   string         `json:"businessName" gorm:"column:bunam"`
	FunctionName   string         `json:"functionName" gorm:"-"`
	FunctionAuthor string         `json:"functionAuthor" gorm:"-"`
	GenType        string         `json:"genType" gorm:"-"`
	GenPath        string         `json:"genPath" gorm:"-"`
	Options        string         `json:"options" gorm:"-"`
	CreateBy       string         `json:"-" gorm:"column:cruid"`
	CreateTime     utils.JsonTime `json:"createTime" gorm:"column:crtim;type:datetime;autoCreateTime"`
	UpdateBy       string         `json:"-" gorm:"column:upuid"`
	UpdateTime     utils.JsonTime `json:"updateTime" gorm:"column:uptim;type:datetime;autoCreateTime"`
	Remark         string         `json:"remark" gorm:"column:remark"`
}

// TableName 指定数据库表名称
func (GenTable) TableName() string {
	return "tool_code_table"
}

type GenTableColumn struct {
	ColumnId      int64          `json:"columnId" gorm:"primaryKey;column:column_id"`
	TableId       int64          `json:"tableId" gorm:"column:tabid"`
	ColumnName    string         `json:"columnName" gorm:"column:name"`
	ColumnComment string         `json:"columnComment" gorm:"column:notes"`
	ColumnType    string         `json:"columnType" gorm:"column:type"`
	JavaType      string         `json:"javaType" gorm:"-"`
	JavaField     string         `json:"javaField" gorm:"-"`
	IsPk          string         `json:"isPk" gorm:"-"`
	IsIncrement   string         `json:"isIncrement" gorm:"-"`
	IsRequired    string         `json:"isRequired" gorm:"-"`
	IsInsert      string         `json:"isInsert" gorm:"-"`
	IsEdit        string         `json:"isEdit" gorm:"-"`
	IsList        string         `json:"isList" gorm:"-"`
	IsQuery       string         `json:"isQuery" gorm:"-"`
	QueryType     string         `json:"queryType" gorm:"-"`
	HtmlType      string         `json:"htmlType" gorm:"-"`
	DictType      string         `json:"dictType" gorm:"-"`
	Sort          string         `json:"sort" gorm:"column:ornum"`
	CreateBy      string         `json:"createBy" gorm:"column:cruid"`
	CreateTime    utils.JsonTime `json:"createTime" gorm:"column:crtim;type:datetime"`
	UpdateBy      string         `json:"updateBy" gorm:"column:upuid"`
	UpdateTime    utils.JsonTime `json:"updateTime" gorm:"column:uptim;type:datetime"`
}

// TableName 指定数据库表名称
func (GenTableColumn) TableName() string {
	return "tool_code_field"
}

type GenTableVO struct {
	TableId        string             `json:"tableId" gorm:"table_id"`
	Table_Name     string             `json:"tableName,omitempty" gorm:"table_name"`
	TableComment   string             `json:"tableComment" gorm:"table_comment"`
	SubTableName   string             `json:"subTableName" gorm:"sub_table_name"`
	SubTableFkName string             `json:"subTableFkName" gorm:"sub_table_fk_name"`
	ClassName      string             `json:"className" gorm:"class_name"`
	TplCategory    string             `json:"tplCategory" gorm:"tpl_category"`
	PackageName    string             `json:"packageName" gorm:"package_name"`
	ModuleName     string             `json:"moduleName" gorm:"module_name"`
	BusinessName   string             `json:"businessName" gorm:"business_name"`
	FunctionName   string             `json:"functionName" gorm:"function_name"`
	FunctionAuthor string             `json:"functionAuthor" gorm:"function_author"`
	GenType        string             `json:"genType" gorm:"gen_type"`
	GenPath        string             `json:"genPath" gorm:"gen_path"`
	Options        string             `json:"options" gorm:"options"`
	Fields         []GenTableColumnVO `json:"fields"`
}

type GenTableColumnVO struct {
	TableId        string `json:"tableId" gorm:"table_id"`
	Table_Name     string `json:"tableName,omitempty" gorm:"table_name"`
	TableComment   string `json:"tableComment" gorm:"table_comment"`
	SubTableName   string `json:"subTableName" gorm:"sub_table_name"`
	SubTableFkName string `json:"subTableFkName" gorm:"sub_table_fk_name"`
	ClassName      string `json:"className" gorm:"class_name"`
	TplCategory    string `json:"tplCategory" gorm:"tpl_category"`
	PackageName    string `json:"packageName" gorm:"package_name"`
	ModuleName     string `json:"moduleName" gorm:"module_name"`
	BusinessName   string `json:"businessName" gorm:"business_name"`
	FunctionName   string `json:"functionName" gorm:"function_name"`
	FunctionAuthor string `json:"functionAuthor" gorm:"function_author"`
	GenType        string `json:"genType" gorm:"gen_type"`
	GenPath        string `json:"genPath" gorm:"gen_path"`
	Options        string `json:"options" gorm:"options"`
	ColumnId       string `json:"columnId" gorm:"column_id"`
	ColumnName     string `json:"columnName" gorm:"column_name"`
	ColumnComment  string `json:"columnComment" gorm:"column_comment"`
	ColumnType     string `json:"columnType" gorm:"column_type"`
	JavaType       string `json:"javaType" gorm:"java_type"`
	FieldName      string `json:"fieldName"`
	JavaField      string `json:"javaField" gorm:"java_field"`
	IsPk           string `json:"isPk" gorm:"is_pk"`
	IsIncrement    string `json:"isIncrement" gorm:"is_increment"`
	IsRequired     string `json:"isRequired" gorm:"is_required"`
	IsInsert       string `json:"isInsert" gorm:"is_insert"`
	IsEdit         string `json:"isEdit" gorm:"is_edit"`
	IsList         string `json:"isList" gorm:"is_list"`
	IsQuery        string `json:"isQuery" gorm:"is_query"`
	QueryType      string `json:"queryType" gorm:"query_type"`
	HtmlType       string `json:"htmlType" gorm:"html_type"`
	DictType       string `json:"dictType" gorm:"dict_type"`
	Sort           string `json:"sort" gorm:"sort"`
}

type EditGenTableVO struct {
	GenTable
	Tree    bool             `json:"tree"`
	Crud    bool             `json:"crud"`
	Sub     bool             `json:"sub"`
	Columns []GenTableColumn `json:"columns"`
}
