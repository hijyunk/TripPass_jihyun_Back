import os
import uvicorn
from fastapi import FastAPI,status, File, UploadFile, Form, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import datetime as datetime
from models import user, myTrips, joinRequests, tripPlans, crew
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import json
from typing import Optional
import base64
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import json

app = FastAPI()
origins =[
    "*"
]
BASE_DIR = os.path.dirname(os.path.relpath("./"))
secret_file = os.path.join(BASE_DIR, 'secret.json')

with open(secret_file) as f:
    secrets = json.loads(f.read())

def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)


PORT = get_secret("MYSQL_PORT")
SQLUSERNAME = get_secret("MYSQL_USER_NAME")
SQLPASSWORD = get_secret("MYSQL_PASSWORD")
SQLDBNAME = get_secret("MYSQL_DB_NAME")
HOSTNAME = get_secret("MYSQL_HOST")

DB_URL = f'mysql+pymysql://{SQLUSERNAME}:{SQLPASSWORD}@{HOSTNAME}:{PORT}/{SQLDBNAME}'

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용. 필요에 따라 변경 가능.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class db_conn:
    def __init__(self):
        self.engine = create_engine(DB_URL, pool_recycle=500)

    def sessionmaker(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session
    
    def connection(self):
        conn = self.engine.connection()
        return conn
sqldb = db_conn()
session = sqldb.sessionmaker()

@app.get('/')
async def healthCheck():
    return "OK"

@app.get('/getUser', description="mySQL user Table 접근해서 정보 가져오기, userId는 선택사항")
async def getUserTable(userId: str = None):
    try:
        query = session.query(user)
        if userId is not None:
            query = query.filter(user.userId == userId)
        user_data = query.all()
        results = []
        for userdata in user_data:
            user_dict = {
                "userId": userdata.userId,
                "id": userdata.id,
                "passwd": userdata.passwd,
                "nickname": userdata.nickname,
                "birthDate": userdata.birthDate,
                "sex": userdata.sex,
                "personality": userdata.personality,
                "profileImage": base64.b64encode(userdata.profileImage).decode('utf-8') if userdata.profileImage else None,
                "mainTrip": userdata.mainTrip
            }
            results.append(user_dict)
        return {"result code": 200, "response": results}
    finally:
        session.close()

@app.get('/getMyTrips', description = "mySQL myTrips Table 접근해서 정보 가져오기, tripId는 선택사항")
async def getMyTripsTable(userId: str = None):
    try:
        query = session.query(myTrips)
        if userId is not None:
            query = query.filter(myTrips.userId == userId)
        mytrips_data = query.all()
        results = []
        for mytrip in mytrips_data:
            mytrip_dict = {
                "tripId": mytrip.tripId,
                "userId": mytrip.userId,
                "title": mytrip.title,
                "contry": mytrip.contry,
                "city": mytrip.city,
                "startDate": mytrip.startDate,
                "endDate": mytrip.endDate,
                "memo": mytrip.memo,
                "banner": base64.b64encode(mytrip.banner).decode('utf-8') if mytrip.banner else None,
                
            }
            results.append(mytrip_dict)
        return {"result code": 200, "response": results}
    finally:
        session.close()

@app.get('/getTripPlans', description = "mySQL tripPlans Table 접근해서 정보 가져오기, tripId는 선택사항")
async def getTripPlansTable(tripId: str = None):
    try:
        query = session.query(tripPlans)
        if tripId is not None:
            query = query.filter(tripPlans.tripId == tripId)
        tripplans_data = query.all()
        return {"result code": 200, "response": tripplans_data}
    finally:
        session.close()

#tripplan 날짜별로 가져올거야 지영아 알겠지? 그니까 어디서 써야해 new crew만들때 쓰면 돼~!
@app.get('/getTripPlansDate', description = "mySQL tripPlans Table 접근해서 정보 가져오기, date, userId 필수사항")
async def getTripPlansDateTable(date: str , userId : str):
    try:
        query = session.query(tripPlans)
        if date is not None and userId is not None:
            query = query.filter(tripPlans.date == date and tripPlans.userId == userId)
        tripplans_data = query.all()
        return {"result code": 200, "response": tripplans_data}
    finally:
        session.close()

@app.get('/getCrew', description = "mySQL crew Table 접근해서 정보 가져오기, crewId는 선택사항")
async def getCrewTable(crewId: str = None):
    try:
        query = session.query(crew)
        if crewId is not None:
            query = query.filter(crew.crewId == crewId)
        crew_data = query.all()
        results = []
        for crews in crew_data:
            crew_dict = {
                "crewId": crews.crewId,
                "planId": crews.planId,
                "tripId": crews.tripId,
                "title": crews.title,
                "contact": crews.contact,
                "note": crews.note,
                "numOfMate": crews.numOfMate,
                "banner": base64.b64encode(crews.banner).decode('utf-8') if crews.banner else None,
                "tripmate": crews.tripmate,
                "sincheongIn": crews.sincheongIn,
            }
            results.append(crew_dict)
        return {"result code": 200, "response": results}
    finally:
        session.close()


@app.get('/getMyCrew', description = "mySQL crew Table 접근해서 정보 가져오기, userId, tripId 필수로 넣기 ")
async def getMyCrewTable( tripId : str, userId : str):
    try:
        query = session.query(crew)
        query = query.filter(and_(crew.tripId == tripId, crew.tripmate.like(f"%{userId}%")))
        print(crew.tripmate.like(f"%{userId}%"))
        crew_data = query.all()
        results = []
        for crews in crew_data:
            query = session.query(tripPlans)
            query = query.filter(tripPlans.planId == crews.planId)
            tripplans_data = query.first()
            query = session.query(myTrips)
            query = query.filter(myTrips.tripId == crew.tripId)
            mytrips_data = query.first()
            crew_dict = {
                "crewId": crews.crewId,
                "planId": crews.planId,
                "userId": tripplans_data.userId,
                "tripId": crews.tripId,
                "date": tripplans_data.date,
                "time": tripplans_data.time,
                "place": tripplans_data.place,
                "title": crews.title,
                "contact": crews.contact,
                "note": crews.note,
                "numOfMate": crews.numOfMate,
                "banner": base64.b64encode(crews.banner).decode('utf-8') if crews.banner else None,
                "tripmate": crews.tripmate,
                "sincheongIn": crews.sincheongIn,
                "address": tripplans_data.address,
                "latitude": tripplans_data.latitude,
                "longitude": tripplans_data.longitude,
                "contry": mytrips_data.contry,
                "city": mytrips_data.city
            }
            results.append(crew_dict)
        return {"result code": 200, "response": results}
    finally:
        session.close()


@app.get('/getCrewCalc', description="mySQL crew Table 접근해서 정보 가져오기, date, contry, city 입력 필수")
async def getCrewTableCalc(date: str = None, contry: str = None, city: str = None):
    # 요청 파라미터가 모두 제공되었는지 확인
    if not date or not contry or not city:
        raise HTTPException(status_code=400, detail="date, contry, and city parameters are required")
    
    
    try:
        # tripPlans 테이블에서 date가 일치하고 crewId가 null이 아닌 플랜들을 가져오기
        tripplans_query = session.query(tripPlans).filter(tripPlans.date == date, tripPlans.crewId != None)
        tripplans_data = tripplans_query.all()
        
        if not tripplans_data:
            raise HTTPException(status_code=404, detail="No trip plans found for the given date")

        results = []
        
        # 가져온 tripPlans 데이터에서 각 트립 플랜의 tripId를 사용하여 myTrips 테이블에서 검색
        for plan in tripplans_data:
            mytrips_query = session.query(myTrips).filter(myTrips.tripId == plan.tripId, myTrips.contry == contry, myTrips.city == city)
            mytrips_data = mytrips_query.first()
            
            if mytrips_data:
                # 관련된 crew 데이터 조회
                crew_query = session.query(crew).filter(crew.planId == plan.planId).first()
                
                if crew_query:
                    crew_dict = {
                        "crewId": crew_query.crewId,
                        "planId": crew_query.planId,
                        "userId": plan.userId,
                        "tripId": crew_query.tripId,
                        "date": plan.date,
                        "time": plan.time,
                        "place": plan.place,
                        "title": crew_query.title,
                        "contact": crew_query.contact,
                        "note": crew_query.note,
                        "numOfMate": crew_query.numOfMate,
                        "banner": base64.b64encode(crew_query.banner).decode('utf-8') if crew_query.banner else None,
                        "tripmate": crew_query.tripmate,
                        "sincheongIn": crew_query.sincheongIn,
                        "address": plan.address,
                        "latitude": plan.latitude,
                        "longitude": plan.longitude,
                        "contry": mytrips_data.contry,
                        "city": mytrips_data.city
                    }
                    # 결과 리스트에 추가
                    results.append(crew_dict)
        
        if not results:
            raise HTTPException(status_code=404, detail="No matching crew data found")

        # 최종 결과 반환
        return {"result code": 200, "response": results}
    except Exception as e:
        # 예외 발생 시 500 에러 반환
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 데이터베이스 세션 종료
        session.close()

@app.get('/getJoinRequests', description = "mySQL joinRequests Table 접근해서 정보 가져오기, joinId는 선택사항")
async def getJoinRequestsTable(requestId: str = None):
    try:
        query = session.query(joinRequests)
        if requestId is not None:
            query = query.filter(joinRequests.requestId == requestId)
        joinrequests_data = query.all()
        results = []
        for join in joinrequests_data:
            join_dict = {
                "requestId": join.requestId,
                "userId": join.userId,
                "tripId": join.tripId,
                "crewId": join.crewId,
                "status": join.status
            }
            results.append(join_dict)
        return {"result code": 200, "response": results}
    finally:
        session.close()

# @app.get('/getCrewRecommend', description = "mySQL crew Table 접근해서 정보 가져오기, 날짜, 도시 입력시 그거 기준으로 가져옴")
# async def getCrewRecommendTable(contry: str, city: str):
#     try:

@app.post('/insertUser', description="mySQL user Table에 추가, userId는 uuid로 생성")
async def insertUserTable(
    id: str = Form(...), 
    passwd: str = Form(...), 
    nickname: str = Form(...),
    birthDate: str = Form(...),
    sex: str = Form(...),
    personality: str = Form(None),
    profileImage: UploadFile = File(None),
    mainTrip: str = Form(None)
    
):
    
    image_data = await profileImage.read() if profileImage else None
    try:
        userId = str(uuid.uuid4())
        new_user = user(userId=userId, id=id, passwd=passwd, nickname=nickname, profileImage=image_data, birthDate=birthDate, sex=sex, personality=personality,
        mainTrip=mainTrip)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return {"result code": 200, "response": userId}
    
    finally:
        session.close()

@app.post('/insertmyTrips', description="mySQL myTrips Table에 추가, tripId는 uuid로 생성")
async def insertMyTripsTable(
    userId: str = Form(...),
    title: str = Form(...),
    contry: str = Form(...),
    city: str = Form(...),
    startDate: str = Form(...),
    endDate: str = Form(...),
    memo: str = Form(None),
    banner: UploadFile = File(None)
):
    image_data = await banner.read() if banner else None
    try:
        tripId = str(uuid.uuid4())
        new_trip = myTrips(tripId=tripId, userId=userId, title=title, contry=contry, city=city, startDate=startDate, endDate=endDate, memo=memo, banner=image_data)
        user_record = session.query(user).filter(user.userId == userId).first()
        if user_record and user_record.mainTrip is None:
            user_record.mainTrip = tripId
            session.commit()
        
        session.add(new_trip)
        session.commit()
        session.refresh(new_trip)
        return {"result code": 200, "response": tripId}

        
    finally:
        session.close()


@app.post('/insertTripPlans', description="mySQL tripPlans Table에 추가, planId는 uuid로 생성")
async def insertTripPlansTable(
    userId :  str = Form(...),
    tripId :  str = Form(...),
    title :  str = Form(...),
    date : str = Form(...),
    time : str = Form(...),
    place :  str = Form(...),
    address : str = Form(...),
    latitude : str = Form(...),
    longitude : str = Form(...),
    description : str = Form(...),
    crewId : str = Form(None)
):
    try:
        planId = str(uuid.uuid4())
        new_tripPlan = tripPlans(planId=planId, userId=userId, tripId=tripId, title=title, date=date, time=time, place=place, address=address, latitude=latitude, longitude=longitude, description=description, crewId=crewId)
        session.add(new_tripPlan)
        session.commit()
        session.refresh(new_tripPlan)
        return {"result code": 200, "response": planId}
    finally:
        session.close()

@app.post('/insertCrew', description="mySQL crew Table에 추가, crewId는 uuid로 생성, insert data 중 일부는 tripPlans planId를 이용해 가져오는거임")
async def insertCrewTable(
    planId : str = Form(...),
    title : str = Form(...),
    contact : str =Form(...),
    note : str = Form(...),
    numOfMate : str = Form(...),
    banner : UploadFile = File(None)
):
    image_data = await banner.read() if banner else None
    try:
        query = session.query(tripPlans)
        query = query.filter(tripPlans.planId == planId)
        tripplans_data = query.all()
        userId = tripplans_data[0].userId
        tripId = tripplans_data[0].tripId
        mytrips_data = session.query(myTrips).filter(myTrips.tripId == tripId).first()
        
        new_crew = crew(
            crewId = str(uuid.uuid4()), 
            planId = planId,
            tripId = tripId,
            title = title,
            contact = contact,
            note = note,
            numOfMate = numOfMate,
            banner = image_data,
            tripmate = userId
        )
        tripplans_data[0].crewId = new_crew.crewId
        session.add(new_crew)
        session.commit()
        session.refresh(new_crew)
        return {"result code": 200, "response": new_crew.crewId}
    finally:
        session.close()
    
@app.post('/insertJoinRequests', description="mySQL joinRequests Table에 추가, requestId는 auto increment로 생성")
async def insertJoinRequestsTable(
    userId : str = Form(...),
    tripId : str = Form(...),
    crewId : str = Form(...)
):
    try:
        new_joinRequest = joinRequests(
            userId=userId, 
            tripId=tripId,
            crewId=crewId,
            status = 0
            )
        query = session.query(crew)
        query = query.filter(crew.crewId == crewId)
        crew_data = query.first()
        session.add(new_joinRequest)
        sincheongIn = crew_data.sincheongIn
        if sincheongIn is None:
            crew_data.sincheongIn = userId
        elif userId in sincheongIn:
            return {"result code": 404, "response": "Already joined"}
        else:
            crew_data.sincheongIn = str(sincheongIn) + "," + userId
        session.commit()
        session.refresh(new_joinRequest)
        return {"result code": 200, "response": crewId}
    finally:
        session.close()


@app.post('/updateUserProfileImage', description="Update profile image in the user table of mySQL")
async def updateUserProfileImage(
    userId: str = Form(...), 
    profileImage: UploadFile = File(...)
):
    image_data = await profileImage.read()

    try:
        query = session.query(user).filter(user.userId == userId)
        user_data = query.first()

        if user_data:
            user_data.profileImage = image_data  
            profile_image_data = base64.b64encode(user_data.profileImage).decode('utf-8')
            session.commit()
            return {
                "userId": user_data.userId,
                "id": user_data.id,
                "nickname": user_data.nickname,
                "birthDate": user_data.birthDate,
                "sex": user_data.sex,
                "personality": user_data.personality,
                "profileImage": profile_image_data,
                "mainTrip": user_data.mainTrip
            }
        else:
            return {"result code": 404, "response": "User not found"}
    except Exception as e:
        session.rollback()
        return {"result code": 500, "response": str(e)}
    finally:
        session.close()

@app.post('/updateUserPasswd', description="mySQL user Table의 비밀번호 업데이트")
async def updateUserProfileImage(
    userId: str = Form(...), 
    passwd : str = Form(...)
):
    try:
        query = session.query(user).filter(user.userId == userId)
        user_data = query.first()

        if user_data:
            user_data.passwd = passwd
            session.commit()
            return {"result code": 200, "response": passwd}
        else:
            return {"result code": 404, "response": "User not found"}
    except Exception as e:
        session.rollback()
        return {"result code": 500, "response": str(e)}
    finally:
        session.close()


@app.post('/updateUserPersonality', description="mySQL user Table의 여행 성향 업데이트")
async def updateUserPersonality(
    userId: str = Form(...), 
    personality : str = Form(...)
):
    try:
        query = session.query(user).filter(user.userId == userId)
        user_data = query.first()

        if user_data:
            user_data.personality = personality
            session.commit()
            return {"result code": 200, "response": personality}
        else:
            return {"result code": 404, "response": "User not found"}
    except Exception as e:
        session.rollback()
        return {"result code": 500, "response": str(e)}
    finally:
        session.close()

@app.post('/updateMyTripsMemo', description="mySQL trip Table의 memo를 업데이트")
async def updateMytripsMemo(
    tripId: str = Form(...), 
    memo : str = Form(...)
):
    try:
        query = session.query(myTrips).filter(myTrips.tripId == tripId)
        trip_data = query.first()

        if trip_data:
            trip_data.memo = memo
            session.commit()
            return {"result code": 200, "response": memo}
        else:
            return {"result code": 404, "response": "User not found"}
    except Exception as e:
        session.rollback()
        return {"result code": 500, "response": str(e)}
    finally:
        session.close()

@app.post('/updateCrewTripMate', description="mySQL crew Table의 tripMate를 업데이트. main page에서 수락 누르면 crew trip mate update 되고 joinRequests status 1로 바뀌고 crew sincheongIn에서 사라짐")
async def updateCrewTripMate(
    crewId: str = Form(...),
    userId: str = Form(...),
    status: int = Form(...),
):
    try:
        # joinRequests 테이블에서 crewId와 userId가 일치하는 레코드를 찾고, status 업데이트
        join_request = session.query(joinRequests).filter(
            joinRequests.crewId == crewId,
            joinRequests.userId == userId
        ).first()

        if not join_request:
            return {"result code": 404, "response": "Join request not found"}

        join_request.status = status
        session.commit()

        # crew 테이블에서 crewId로 크루 찾기
        crew_data = session.query(crew).filter(crew.crewId == crewId).first()
        if not crew_data:
            return {"result code": 404, "response": "Crew not found"}

        # sincheongIn 필드에서 userId 제거
        sincheongIn = crew_data.sincheongIn.split(",") if crew_data.sincheongIn else []
        if userId in sincheongIn:
            sincheongIn.remove(userId)
            if not sincheongIn or sincheongIn == [""]:
                crew_data.sincheongIn = None
            else:
                crew_data.sincheongIn = ",".join(sincheongIn)
        session.commit()

        # status가 1인 경우 (수락 상태)
        if status == 1:
            # tripmate 필드에 userId 추가
            tripmates = crew_data.tripmate.split(",") if crew_data.tripmate else []
            if userId not in tripmates:
                tripmates.append(userId)
                crew_data.tripmate = ",".join(tripmates)
            session.commit()

            # joinRequests 테이블에서 tripId 가져오기
            tripId = join_request.tripId

            # tripPlans 테이블에서 tripId로 계획 찾기
            trip_plans = session.query(tripPlans).filter(tripPlans.tripId == crew_data.tripId).first()
            new_trip_plan = tripPlans(
                planId=str(uuid.uuid4()),
                userId=userId,
                tripId=tripId,
                title=trip_plans.title,
                date=trip_plans.date,
                time=trip_plans.time,
                place=trip_plans.place,
                address=trip_plans.address,
                latitude=trip_plans.latitude,
                longitude=trip_plans.longitude,
                description=trip_plans.description,
                crewId=trip_plans.crewId
            )
            session.add(new_trip_plan)
            session.commit()

        return {"result code": 200, "response": "Operation successful"}
    except Exception as e:
        session.rollback()
        return {"result code": 500, "response": str(e)}
    finally:
        session.close()


# 사용자 로그인 처리
@app.post("/login")
async def login(id: str = Form(...), passwd: str = Form(...), session: session = Depends(sqldb.sessionmaker)):
    try:
        user_data = session.query(user).filter(user.id == id).first()
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        if user_data.passwd != passwd:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        profile_image_data = base64.b64encode(user_data.profileImage).decode('utf-8') if user_data.profileImage else None
        
        return {
            "userId": user_data.userId,
            "id" : user_data.id,
            "nickname": user_data.nickname,
            "birthDate": user_data.birthDate,
            "sex": user_data.sex,
            "personality": user_data.personality,
            "profileImage": profile_image_data,
            "mainTrip": user_data.mainTrip
        }
    finally:
        session.close()

# 세영 user table의 mainTrip 업데이트 myTripPage에서 사용
@app.post("/updateUserMainTrip", description="mySQL user Table의 mainTrip 업데이트, myTripPage에서 사용")
async def update_user_main_trip(request: Request):
    data = await request.json()
    user_id = data.get("userId")
    main_trip = data.get("mainTrip")
    
    if not user_id or not main_trip:
        raise HTTPException(status_code=422, detail="userId and mainTrip are required")
    
    try:
        query = session.query(user).filter(user.userId == user_id)
        user_data = query.first()

        if user_data:
            user_data.mainTrip = main_trip
            session.commit()
            return {"result code": 200, "response": main_trip}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()