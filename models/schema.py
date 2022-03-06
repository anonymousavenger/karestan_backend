import re
from util.validation import Validators, ModelField, BaseParamsSchema, convert_to_datetime,\
 remove_bad_persian_letters, remove_inside_parantheses


class CompanyMain(BaseParamsSchema):
    fa_name: ModelField
    en_name: ModelField
    phone: ModelField
    website: ModelField
    dirname: ModelField
    industy_id: ModelField
    city_id: ModelField
    info: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.industy_id = ModelField(
            field_type=int,
            optional= False
        )
        
        def add_sherkat(strx:str):
            if len(strx) < 4 and strx not in [None, ""]:
                return "شرکت " + strx
            return strx

        self.fa_name = ModelField(
            field_type =  str,
            optional =  False,
            preconverter= lambda x: add_sherkat(remove_inside_parantheses(remove_bad_persian_letters(x))),
            eval =  {
                "_fa": lambda x: Validators.fa_text(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 60" if len(x) > 60 else None,
            }
        )

        self.dirname = ModelField(
            field_type=str,
            optional= False,
            eval={
                "_length": lambda x: "length must be bigger than 4" if len(x) < 4 else None,
                "_valid_text": lambda x: Validators.en_dirname(x)
            },
        )

        

        def add_corp(strx:str):
            if len(strx) < 4 and strx not in [None, ""]:
                return strx + " Corp."
            return strx

        self.en_name = ModelField(
            field_type =  str,
            optional =  False,
            preconverter= lambda x: add_corp(remove_inside_parantheses(remove_bad_persian_letters(x))),
            eval =  {
                "_en": lambda x: Validators.en_company_name(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 60" if len(x) > 50 else None,
            }
        )

        self.city_id = ModelField(
            field_type=int,
            optional= False
        )

        reg = re.compile(f"^(http://)?(.*)$")
        self.website = ModelField(
            field_type =  str,
            optional =  True,
            eval =  {
                "_format": lambda x: Validators.website(x),
                "_length": lambda x: "Website length can't be more than 60 chars" if len(x) > 60 else None
            },
            preconverter= lambda x: reg.search(x).group(2)
        )

        self.phone = ModelField(
            field_type =  str,
            optional =  True,
            eval =  {
                "_format": lambda x: Validators.int_text(x),
                "_length": lambda x: "Phone length must be between 4 and 15 chars" if len(x) < 4 or len(x) > 15 else None,
                "_no_zero": lambda x: "Phone number must not start with zero" if x[0] == '0' else None
            },
            postconverter= lambda x: str(int(x))
        )

        self.info = ModelField(
            field_type= CompanyInfo,
            optional= True
        )

class CompanyInfo(BaseParamsSchema):
    avg_salary: ModelField
    min_salary: ModelField
    max_salary: ModelField
    description: ModelField
    company_size: ModelField
    date_founded: ModelField
    old_review_count: ModelField
    old_interview_count: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.avg_salary = ModelField(
            field_type=float,
            optional= True,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
                "_check_calc": lambda x: "Wrong avg salary amount" if x < self.inputs.get('min_salary',0) or x > self.inputs.get('max_salary',100) else None
            },
            preconverter= lambda x: round(float(x),2)
        )

        self.min_salary = ModelField(
            field_type=float,
            optional= True,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
                "_check_calc": lambda x: "Wrong min salary amount" if x > self.inputs.get('avg_salary',100) or x > self.inputs.get('max_salary',100) else None
            },
            preconverter= lambda x: round(float(x),2)      
        )

        self.max_salary = ModelField(
            field_type=float,
            optional= True,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
                "_check_calc": lambda x: "Wrong max salary amount" if x < self.inputs.get('avg_salary',0) or x < self.inputs.get('min_salary',0) else None
            },
            preconverter= lambda x: round(float(x),2)           
        )

        self.description = ModelField(
            field_type=str,
            optional= True,
            eval={
                "_farsi": lambda x: Validators.fa_text,
                "_bigger": lambda x: "The length of description must be bigger than 20" if len(x) < 20 else None,
                "_smaller": lambda x: "The length of description can't be bigger than 200" if len(x) > 1000 else None,
            }                  
        )
        size_mapper = {
            "VS":"XS",
            "S":"S",
            "M":"M",
            "L":"L",
            "VL":"XL",
        }
        self.company_size = ModelField(
            field_type=str,
            optional= True,
            eval={
                "_none": lambda x: "Invalid company size" if x is None else None
            },
            preconverter= lambda x: size_mapper.get(x.upper()) if x not in size_mapper.values() else x
        )

        self.date_founded = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_before_now": lambda x: Validators.date_compare(x, date=None, order='before')
            },
            preconverter= lambda x: int(x)
        )

        self.old_interview_count  = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_bigger": lambda x: "The count must be bigger than zero" if x < 0 else None
            }            
        )

        self.old_review_count  = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_bigger": lambda x: "The count must be bigger than zero" if x < 0 else None
            }            
        )

class CompanyMainImport(BaseParamsSchema):
    fa_name: ModelField
    en_name: ModelField
    city_slug: ModelField
    phone: ModelField
    website: ModelField
    industy_id: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.industy_id = ModelField(
            field_type=int,
            optional= True
        )
        
        def add_sherkat(strx:str):
            if len(strx) < 4 and strx not in [None, ""]:
                return "شرکت " + strx
            return strx

        self.fa_name = ModelField(
            field_type =  str,
            optional =  False,
            preconverter= lambda x: add_sherkat(remove_inside_parantheses(remove_bad_persian_letters(x))),
            eval =  {
                "_fa": lambda x: Validators.fa_text(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 60" if len(x) > 60 else None,
            }
        )

        def add_corp(strx:str):
            if len(strx) < 4 and strx not in [None, ""]:
                return strx + " Corp."
            return strx

        self.en_name = ModelField(
            field_type =  str,
            optional =  False,
            preconverter= lambda x: add_corp(remove_inside_parantheses(remove_bad_persian_letters(x))),
            eval =  {
                "_en": lambda x: Validators.en_company_name(x),
                "_bigger": lambda x: "The length of company name must be bigger than 4" if len(x) < 4 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 60" if len(x) > 50 else None,
            }
        )

        self.city_slug = ModelField(
            field_type =  str,
            optional =  True,
            preconverter= remove_bad_persian_letters,
            eval =  {
                "_fa": lambda x: Validators.fa_text(x),
                "_bigger": lambda x: "The length of company name must be bigger than 2" if len(x) < 2 else None,
                "_smaller": lambda x: "The length of company name can't be bigger than 32" if len(x) > 32 else None,
            }
        )
        reg = re.compile(f"^(http://)?(.*)$")
        self.website = ModelField(
            field_type =  str,
            optional =  True,
            eval =  {
                "_format": lambda x: Validators.website(x),
                "_length": lambda x: "Website length can't be more than 60 chars" if len(x) > 60 else None
            },
            preconverter= lambda x: reg.search(x).group(2)
        )

        self.phone = ModelField(
            field_type =  str,
            optional =  True,
            eval =  {
                "_format": lambda x: Validators.int_text(x),
                "_length": lambda x: "Phone length must be between 4 and 15 chars" if len(x) < 4 or len(x) > 15 else None,
                "_no_zero": lambda x: "Phone number must not start with zero" if x[0] == '0' else None
            },
            postconverter= lambda x: str(int(x))
        )

class CompanyInfoImport(BaseParamsSchema):
    avg_salary: ModelField
    min_salary: ModelField
    max_salary: ModelField
    dirname: ModelField
    description: ModelField
    company_size: ModelField
    date_founded: ModelField
    old_review_count: ModelField
    old_interview_count: ModelField

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.avg_salary = ModelField(
            field_type=float,
            optional= True,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
                "_check_calc": lambda x: "Wrong avg salary amount" if x < self.inputs['min_salary'] or x > self.inputs['max_salary'] else None
            },
            preconverter= lambda x: round(float(x),2)
        )

        self.min_salary = ModelField(
            field_type=float,
            optional= True,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
                "_check_calc": lambda x: "Wrong min salary amount" if x > self.inputs['avg_salary'] or x > self.inputs['max_salary'] else None
            },
            preconverter= lambda x: round(float(x),2)      
        )

        self.max_salary = ModelField(
            field_type=float,
            optional= True,
            eval={
                "_order": lambda x: "The salary must be btween 1 and 100 million tomans" if x < 1 or x > 100 else None,
                "_check_calc": lambda x: "Wrong max salary amount" if x < self.inputs['avg_salary'] or x < self.inputs['min_salary'] else None
            },
            preconverter= lambda x: round(float(x),2)           
        )

        self.dirname = ModelField(
            field_type=str,
            optional= False,
            eval={
                "_length": lambda x: "length must be bigger than 4" if len(x) < 4 else None,
                "_valid_text": lambda x: Validators.en_dirname(x)
            },
        )

        self.description = ModelField(
            field_type=str,
            optional= True,
            eval={
                "_farsi": lambda x: Validators.fa_text,
                "_bigger": lambda x: "The length of description must be bigger than 20" if len(x) < 20 else None,
                "_smaller": lambda x: "The length of description can't be bigger than 200" if len(x) > 1000 else None,
            }                  
        )
        size_mapper = {
            "VS":"XS",
            "S":"S",
            "M":"M",
            "L":"L",
            "VL":"XL",
        }
        self.company_size = ModelField(
            field_type=str,
            optional= True,
            eval={
                "_none": lambda x: "Invalid company size" if x is None else None
            },
            preconverter= lambda x: size_mapper.get(x.upper()) if x not in size_mapper.values() else x
        )

        date_fmt = "%Y"
        self.date_founded = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_before_now": lambda x: Validators.date_compare(x,format= date_fmt, date=None, order='before')
            },
            preconverter= lambda x: int(convert_to_datetime(x, date_fmt).timestamp())
        )

        self.old_interview_count  = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_bigger": lambda x: "The count must be bigger than zero" if x < 0 else None
            }            
        )

        self.old_review_count  = ModelField(
            field_type=int,
            optional= True,
            eval={
                "_bigger": lambda x: "The count must be bigger than zero" if x < 0 else None
            }            
        )
